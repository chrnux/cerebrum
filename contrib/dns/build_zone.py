#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import os
import re
import sys
import time
import getopt

import cerebrum_path
import cereconf

from Cerebrum import Utils
from Cerebrum.Utils import Factory
from Cerebrum.modules.dns import ARecord, AAAARecord
from Cerebrum.modules.dns import HostInfo
from Cerebrum.modules.dns import DnsOwner
from Cerebrum.modules.dns import IPNumber, IPv6Number
from Cerebrum.modules.dns import CNameRecord
from Cerebrum.modules.dns.Utils import IPCalc
from Cerebrum.modules.dns.IPv6Utils import IPv6Calc

db = Factory.get('Database')()
co = Factory.get('Constants')(db)
#sys.argv.extend(["--logger-level", "DEBUG"])
logger = Factory.get_logger("cronjob")

header_splitter = '; WARNING: This file is autogenerated by buildzone.py\n'
# extra_splitter is used by strip4cmp.py
extra_splitter = '; AUTOGENERATED: do not edit below this line\n'

class ZoneUtils(object):
    re_serial = re.compile(r'(\d+)\s*;\s*Serialnumber')

    def __init__(self, zone, origin=None):
        self._zone = zone
        self._as_reversemap = False
        if zone is None:
            self._as_reversemap = True
            self.__origin = origin

        
    def exp_name(self, name, no_dot=False):
        ret = name
        if not name[-1] == '.':
            ret = name+self._zone.postfix
        if no_dot and ret[-1] == '.':
            ret = ret[:-1]
        return ret


    def trim_name(self, name):
        if name.endswith(self._zone.postfix):
            return name[:-len(self._zone.postfix)]
        return name


    def open(self, fname):
        self._file = Utils.AtomicFileWriter(fname, "w")
        self._fname = fname


    def write_heads(self, heads, data_dir):
        """Writes the zone-file header file(s), re-using the old
        serial number"""

        self._file.write(header_splitter)
        serial = self._read_update_serial(self._fname)
        logger.debug("write_heads; serial: %s" % serial)
        first = True
        for h in heads:
            logger.debug("Looking at header-file '%s'" % h)
            fin = file(h, "r")
            lines = []
            for line in fin:
                m = ZoneUtils.re_serial.search(line)
                if m:
                    line = "%30s ; Serialnumber\n" % serial
                lines.append(line)
            if first and self._as_reversemap and not [
                x for x in lines if x.startswith('$ORIGIN')]:
                lines.insert(0, self.__origin)
            self._file.write("".join(lines))
            fin.close()
            first = False
        self._file.write(extra_splitter)


    def close(self):
        self._file.close(dont_rename=True)
        if self._file.replaced_file:
            self._read_update_serial(self._file._tmpname, update=True)
            os.rename(self._file._tmpname, self._file._name)


    def write(self, s):
        self._file.write(s)

    def _read_update_serial(self, fname, update=False):
        """Parse existing serial in zonefile, and optionally updates
        the serial. Returns the serial used."""

        all_lines = []
        if os.path.exists(fname):
            for line in open(fname):
                m = ZoneUtils.re_serial.search(line)
                if m:
                    serial = m.group(1)
                    logger.debug("Old serial: %s" % serial)
                    if not update:
                        return serial
                    if serial[:-2] == time.strftime('%Y%m%d'):
                        serial = int(serial) + 1
                    else:
                        serial = time.strftime('%Y%m%d') + '01'
                    logger.debug("New serial: %s" % serial)
                    line = "%30s ; Serialnumber\n" % serial
                all_lines.append(line)
        if not update:
            # First time this zone is written
            serial = time.strftime('%Y%m%d') + '01'
            logger.debug("First time; new serial used: %s" % serial)
            return serial
        # Rewrite the entire file in case the serial line length has changed
        f = Utils.AtomicFileWriter(fname, 'w')
        f.write("".join(all_lines))
        f.close()



class ForwardMap(object):
    # Currently we first read all required data into memory before writing
    # the new zone file.  It is assumed that it will be faster, since
    # fewver sql queries will be needed.

    def __init__(self, zone):
        self.zu = ZoneUtils(zone)
        self.a_records = {}
        self.a_records_by_dns_owner = {}
        self.aaaa_records = {}
        self.aaaa_records_by_dns_owner = {}
        self.hosts = {}
        self.cnames = {}
        self.mx_sets = {}
        self.owner_id2mx_set = {}
        self.dnsowner2txt_record = {}
        self.srv_records = {}
        logger.debug("Getting zone data")
        self._get_zone_data(zone)
        logger.debug("done getting zone data")

      
    def _get_zone_data(self, zone):
        # ARecord has key=a_record_id
        # HostInfo, SrvRecord has key=dns_owner_id
        # CnameRecords key=target_owner_id
        # entity2txt, entity2note has_key=entity_id
        for row in ARecord.ARecord(db).list_ext(zone=zone):
            id = int(row['dns_owner_id'])
            if self.a_records_by_dns_owner.has_key(id):
                self.a_records_by_dns_owner[id] += [row]
            else:
                self.a_records_by_dns_owner[id] = [row]

            # Following dict is populated to support HostFile
            self.a_records[int(row['a_record_id'])] = row
        logger.debug("... arecords")
        
        for row in AAAARecord.AAAARecord(db).list_ext(zone=zone):
            id = int(row['dns_owner_id'])
            if self.aaaa_records_by_dns_owner.has_key(id):
                self.aaaa_records_by_dns_owner[id] += [row]
            else:
                self.aaaa_records_by_dns_owner[id] = [row]
            # Following dict is populated to support HostFile
            self.aaaa_records[int(row['aaaa_record_id'])] = row
        logger.debug("... aaaarecords")

        for row in HostInfo.HostInfo(db).list(zone=zone):
            # Unique constraint on dns_owner_id
            self.hosts[int(row['dns_owner_id'])] = row

        logger.debug("... hosts")
        for row in CNameRecord.CNameRecord(db).list_ext(zone=zone):
            # TBD:  skal vi ha unique constraint p� dns_owner?
            self.cnames.setdefault(int(row['target_owner_id']), []).append(row)
        logger.debug("... cnames")

        # From mix-in classes
        for row in DnsOwner.MXSet(db).list_mx_sets():
            self.mx_sets.setdefault(int(row['mx_set_id']), []
                                    ).append(row)

        logger.debug("... mx_sets")
        for row in DnsOwner.DnsOwner(db).list(zone=zone):
            self.owner_id2mx_set[int(row['dns_owner_id'])] = int(
                row['mx_set_id'] or 0)

        logger.debug("... mx_set owners")

        for row in DnsOwner.DnsOwner(db).list_general_dns_records(
            field_type=co.field_type_txt, zone=zone):
            self.dnsowner2txt_record[int(row['dns_owner_id'])] = row
        logger.debug("... txt reocrds")

        for row in DnsOwner.DnsOwner(db).list_srv_records(zone=zone):
            # We want them listed in the same place
            # TODO: while doing that, we want it below the first target_owner_id
            self.srv_records.setdefault(
                int(row['service_owner_id']), []).append(row) 
        logger.debug("... srv records")

    def generate_zone_file(self, fname, heads, data_dir):
        logger.debug("Generating zone file")
        self.zu.open(os.path.join(data_dir, os.path.basename(fname)))
        self.zu.write_heads(heads, data_dir)

        def aaaa_cmp(x,y):
            if IPv6Calc.ip_to_long(self.aaaa_records[x]['aaaa_ip']) == \
                    IPv6Calc.ip_to_long(self.aaaa_records[y]['aaaa_ip']):
                return 0
            elif IPv6Calc.ip_to_long(self.aaaa_records[x]['aaaa_ip']) < \
                    IPv6Calc.ip_to_long(self.aaaa_records[y]['aaaa_ip']):
                return -1
            else:
                return 1

        ar = self.a_records.keys()
        ar.sort(lambda x,y: int(self.a_records[x]['ipnr'] -
                                   self.a_records[y]['ipnr']))

        aaaar = self.aaaa_records.keys()
        aaaar.sort(aaaa_cmp)

        order = ar + aaaar

        # If multiple A- or AAAA-records have the same name with different IP,
        # the dns_owner data is only shown for the first IP.
        shown_owner = {}
        prev_name = None
        for a_id in order:
            line = ''
            
            ar = self.a_records.get(a_id, None)
            aaaar = self.aaaa_records.get(a_id, None)
            
            if ar is not None:
                name = self.zu.trim_name(ar['name'])
                line += "%s\t%s\tA\t%s\n" % (
                    name, ar['ttl'] or '', ar['a_ip'])

            elif aaaar is not None:
                name = self.zu.trim_name(aaaar['name'])
                ar = aaaar

                line += "%s\t%s\tAAAA\t%s\n" % (
                    name, ar['ttl'] or '', ar['aaaa_ip'])

            dns_owner_id = int(ar['dns_owner_id']) 
            if shown_owner.has_key(dns_owner_id):
                self.zu.write(line)
                continue
            shown_owner[dns_owner_id] = True
            #logger.debug2("A: %s, owner=%s" % (a_id, dns_owner_id))
            if self.hosts.has_key(dns_owner_id):
                line += "\t%s\tHINFO\t%s\n" % (
                    self.hosts[dns_owner_id]['ttl'] or '',
                    self.hosts[dns_owner_id]['hinfo'])
            #logger.debug("own=%i %s" % (dns_owner_id, str(owner_id2mx_set[dns_owner_id])))
            if self.owner_id2mx_set.get(dns_owner_id, None):
                for mx_info in self.mx_sets[self.owner_id2mx_set[dns_owner_id]]:
                    line += "\t%s\tMX\t%s\t%s\n" % (
                        mx_info['ttl'] or '', mx_info['pri'],
                        self.zu.exp_name(mx_info['target_name']))
            txt = self.dnsowner2txt_record.get(dns_owner_id, None)
            if txt:
                line += "\t%s\tTXT\t\"%s\"\n" % (txt['ttl'] or '', txt['data'])

            for c_ref in self.cnames.get(dns_owner_id, []):
                line += "%s\t%s\tCNAME\t%s\n" % (
                    c_ref['name'], c_ref['ttl'] or '',
                    self.zu.exp_name(c_ref['target_name']))
                # for machines with multiple a-records and cnames, the
                # cnames will be listed before the last a-records.
                prev_name = ''
            self.zu.write(line)
        self.zu.write('; End of a-record owned entries\n')
        logger.debug("Check remaining data")
        for row in DnsOwner.DnsOwner(db).list():
            line = ''
            # Check for any remaining data.  Should only be srv_records
            # and cnames with foreign targets
            name = self.zu.trim_name(row['name'])
            for s_ref in self.srv_records.get(row['dns_owner_id'], []):
                line += "%s\t%s\tSRV\t%i\t%i\t%i\t%s\n" % (name,
                    s_ref['ttl'] or '', s_ref['pri'], s_ref['weight'],
                    s_ref['port'], self.zu.exp_name(s_ref['target_name']))
                name = ''
            if not shown_owner.has_key(row['dns_owner_id']):
                if self.owner_id2mx_set.get(int(row['dns_owner_id']), None):
                    for mx_info in self.mx_sets[self.owner_id2mx_set[int(row['dns_owner_id'])]]:
                        line += "%s\t%s\tMX\t%s\t%s\n" % (
                            name, mx_info['ttl'] or '', mx_info['pri'],
                            self.zu.exp_name(mx_info['target_name']))
                        name = ''
                for c_ref in self.cnames.get(row['dns_owner_id'], []):
                    line += "%s\t%s\tCNAME\t%s\n" % (
                        c_ref['name'], c_ref['ttl'] or '',
                        self.zu.exp_name(c_ref['target_name']))
            if line:
                self.zu.write(line)
        self.zu.close()
        logger.debug("zone file completed")

class ReverseMap(object):
    def __init__(self, mask):
        self.ip_numbers = {}
        self.a_records = {}
        self.override_ip = {}
        ipu = IPCalc()
        net, mask = mask.split("/")
        self._get_reverse_data(*ipu.ip_range_by_netmask(net, int(mask)))
        tmp = net.split(".")
        if int(mask) < 24:
            net = ".".join(tmp[:2])
        else:
            net = ".".join(tmp[:3])
        self.__prev_origin = self.__net2origin(net)
        self.zu = ZoneUtils(None, self.__prev_origin)

    
    def _get_reverse_data(self, start, stop):
        for row in IPNumber.IPNumber(db).list(start=start, stop=stop):
            self.ip_numbers[int(row['ip_number_id'])] = row

        for row in ARecord.ARecord(db).list_ext(start=start, stop=stop):
            self.a_records.setdefault(int(row['ip_number_id']), []).append(row)

        for row in IPNumber.IPNumber(db).list_override(start=start, stop=stop):
            self.override_ip.setdefault(int(row['ip_number_id']), []).append(row)
        logger.debug("_get_reverse_data -> %i, %i, %i" % (
            len(self.ip_numbers), len(self.a_records), len(self.override_ip)))
        

    def __net2origin(self, ip):
        tmp = ip.split('.')[:3]
        tmp.reverse()
        return '$ORIGIN %s.IN-ADDR.ARPA.\n' % ".".join(tmp)


    def generate_reverse_file(self, fname, heads, data_dir):
        self.zu.open(os.path.join(data_dir, os.path.basename(fname)))
        self.zu.write_heads(heads, data_dir)

        order = self.ip_numbers.keys()
        order.sort(lambda x,y: int(self.ip_numbers[x]['ipnr'] - self.ip_numbers[y]['ipnr']))
        this_net = 'z'
        for ip_id in order:
            if self.override_ip.has_key(ip_id):
                tmp = self.override_ip[ip_id]
            elif self.a_records.has_key(ip_id):
                tmp = self.a_records[ip_id]
            else:
                logger.warn("dangling ip-number %i" % ip_id)
                continue
            a_ip = self.ip_numbers[ip_id]['a_ip']
            if not a_ip.startswith(this_net):
                this_net = a_ip[:a_ip.rfind(".")+1]
                line = self.__net2origin(a_ip)
                if line != self.__prev_origin:
                    self.zu.write(line)
                    self.__prev_origin = line  # avoid dupl. $ORIGIN in /24 net
            a_ip = a_ip[a_ip.rfind(".")+1:]
            for row in tmp:
                if row['name'] is not None:
                    line = "%s\tPTR\t%s\n" % (a_ip, row['name'])
                    self.zu.write(line)
        self.zu.close()

class IPv6ReverseMap(object):
    def __init__(self, mask):
        # TODO: Make this dependent on the netmask?
        self.start = mask + '0000'[:len(mask.split(':')[-1])]
        self.stop = mask + 'ffff'[:len(mask.split(':')[-1])]

        self.ip_numbers = {}
        self.a_records = {}
        self.override_ip = {}
        self.origins = {}
        self._get_reverse_data()

        self.__prev_origin = self.__net2origin(mask)
        self.zu = ZoneUtils(None, self.__prev_origin)



    def _get_reverse_data(self):
        for row in IPv6Number.IPv6Number(db).list(start=self.start,
                                                  stop=self.stop):
            self.ip_numbers[int(row['ipv6_number_id'])] = row

        for row in AAAARecord.AAAARecord(db).list_ext(start=self.start,
                                                      stop=self.stop):
            self.a_records.setdefault(int(row['ipv6_number_id']), []).append(row)

        for row in IPv6Number.IPv6Number(db).list_override(start=self.start,
                                                           stop=self.stop):
            self.override_ip.setdefault(int(row['ipv6_number_id']), []).append(row)
        logger.debug("_get_reverse_ipv6_data -> %i, %i, %i" % (
            len(self.ip_numbers), len(self.a_records), len(self.override_ip)))
   
    # Expand the parts of the adress that are not filled.
    def __expand_ipv6(self, ip):
        ip = ip.split(':')
        eip = []
        for i in range(0, len(ip)):
            if len(ip[i]) < 4:
                tmp = '%4s' % ip[i]
                tmp = tmp.replace(' ', '0')
                eip += [tmp]
            else:
                eip += [ip[i]]
        return ':'.join(eip)

    def __ipv6_reversed_parts(self, ip):
        # Fast check to see if IP is expanded:
        if not len(ip) == 39:
            ip = self.__expand_ipv6(ip)

        # We reverse the IP and strip it of ':'
        rev = ''.join(ip[::-1].split(':'))
        first = '.'.join(rev[:16])
        second = '.'.join(rev[16:])
        # return a tuple with both parts, dotted
        return (first, second)

    def __net2origin(self, net):
            return '$ORIGIN %s.ip6.arpa.\n' % self.__ipv6_reversed_parts(net)[1]

    def generate_reverse_file(self, fname, heads, data_dir):
        self.zu.open(os.path.join(data_dir, os.path.basename(fname)))
        self.zu.write_heads(heads, data_dir)

        for ip_id in self.ip_numbers.keys():
            if self.override_ip.has_key(ip_id):
                tmp = self.override_ip[ip_id]
            elif self.a_records.has_key(ip_id):
                tmp = self.a_records[ip_id]
            else:
                logger.warn("dangling ip-number %i" % ip_id)
                continue

            ip = self.ip_numbers[ip_id]['aaaa_ip']
            rev_ip = self.__ipv6_reversed_parts(ip)

            adrs = []
            for row in tmp:
                if row['name'] is not None:
                    adrs.append("%s\tPTR\t%s\n" % (rev_ip[0], row['name']))
            self.origins.setdefault(rev_ip[1], []).extend(adrs)
        
        def sort_rev_lines(x,y):
            x1 = x[:31][::-1]
            y1 = y[:31][::-1]
            if x1 == y1:
                return 0
            elif x1 < y1:
                return -1
            else:
                return 1

        for key in sorted(self.origins.keys(), cmp=sort_rev_lines):
            self.zu.write('$ORIGIN %s.ip6.arpa.\n' % key)
            for line in sorted(self.origins[key], cmp=sort_rev_lines):
                self.zu.write(line)
        self.zu.close()

class HostsFile(object):
    MAX_LINE_LENGTH = 1000
    def __init__(self, zone):
        self._zone = zone
        self.zu = ZoneUtils(zone)
        

    def _exp_name(self, name):
        """Returns name name.uio.no or only FQDN if name is from
        another zone"""
        trimmed = self.zu.trim_name(name)
        if name != trimmed:
            return "%s %s" % (trimmed, name[:-1])
        return name[:-1]

    
    def generate_hosts_file(self, fname, with_comments=False):
        f = Utils.AtomicFileWriter(fname, "w")
        
        # IPv4
        fm = ForwardMap(self._zone)
        order = fm.a_records.keys()
        order.sort(lambda x,y: int(fm.a_records[x]['ipnr'] - fm.a_records[y]['ipnr']))

        entity_id2comment = {}
        if with_comments:
            for row in DnsOwner.DnsOwner(db).list_traits(co.trait_dns_comment):
                entity_id2comment[int(row['entity_id'])] = ' # ' + row['strval']

        # If multiple A-records have the same name with different IP, the
        # dns_owner data is only shown for the first IP.
        shown_owner = {}
        prev_name = None
        for a_id in order:
            line = ''
            a_ref = fm.a_records[a_id]

            prefix = '%s\t%s' % (a_ref['a_ip'], self._exp_name(a_ref['name']))
            line = ''
            names = [ ]

            dns_owner_id = int(a_ref['dns_owner_id'])
            if shown_owner.has_key(dns_owner_id):
                # raise ValueError, "%s already shown?" % a_ref['name']
                continue
            shown_owner[dns_owner_id] = True

            for c_ref in fm.cnames.get(dns_owner_id, []):
                names.append(c_ref['name'])

            line += " " + " ".join([self._exp_name(n) for n in names])
            line += entity_id2comment.get(int(a_ref['dns_owner_id']), '')

            f.write(self._wrap_line(prefix, line))

        # IPv6
        order = fm.aaaa_records.keys()

        entity_id2comment = {}
        if with_comments:
            for row in DnsOwner.DnsOwner(db).list_traits(co.trait_dns_comment):
                entity_id2comment[int(row['entity_id'])] = ' # ' + row['strval']

        # If multiple A-records have the same name with different IP, the
        # dns_owner data is only shown for the first IP.
        shown_owner = {}
        prev_name = None
        for a_id in order:
            line = ''
            a_ref = fm.aaaa_records[a_id]

            prefix = '%s\t%s' % (a_ref['aaaa_ip'], self._exp_name(a_ref['name']))
            line = ''
            names = [ ]

            dns_owner_id = int(a_ref['dns_owner_id'])
            if shown_owner.has_key(dns_owner_id):
                # raise ValueError, "%s already shown?" % a_ref['name']
                continue
            shown_owner[dns_owner_id] = True

            for c_ref in fm.cnames.get(dns_owner_id, []):
                names.append(c_ref['name'])

            line += " " + " ".join([self._exp_name(n) for n in names])
            line += entity_id2comment.get(int(a_ref['dns_owner_id']), '')

            f.write(self._wrap_line(prefix, line))

        f.close()


    def _wrap_line(self, prefix, line):
        delim = ' '
        ret = ''
        maxlen = HostsFile.MAX_LINE_LENGTH - (len(prefix) + 1)
        if len(line) > maxlen:
            idx = line.find(' #')
            if idx != -1:
                line = line[:idx]
        while len(line) > maxlen:
            maxlen = HostsFile.MAX_LINE_LENGTH - (len(prefix) + 1)
            if len(line) <= maxlen:
                pos = 0
            else:
                pos = line.index(delim, len(line) - maxlen)
            ret += "%s%s%s\n" % (prefix, ' ', line[pos+1:])
            line = line[:pos]
        return ret + "%s%s%s\n" % (prefix, ' ', line)



def usage(exitcode=0):
    print """Usage: [options]
    Builds new zone file.

    -h | --help: help
    -Z | --zone zone: use with -b to specify zone
    -m | --mask net/mask: use with -r to specify iprange
    -n | --mask6 mask: use with -s to specify range
    -b | --build filename: write new zonefile to filename
    -r | --reverse filename: write new reverse map to filename
    -s | --reverse6 filename: write new IPv6 reverse map to filename
    -d | --dir dir: store .status/.serial files in this dir (default:
      same dir as filename)
    --head filename: header for the static part of the zone-file.  May
      be repeated.  One line must end with '\d+ ; Serialnumber'
      required for -b/-r
    --hosts filename: write new hosts file to filename
    -R : resets head list
    """
    sys.exit(exitcode)


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'b:hr:s:Z:m:n:Rd:', [
            'help', 'build=', 'reverse=', 'reverse6=', 'hosts=', 'head=',
            'zone=', 'mask=', 'mask6=', 'dir=', 'comments'])
    except getopt.GetoptError, e:
        print e
        usage(1)

    heads = []
    data_dir = None
    with_comments = False
    for opt, val in opts:
        if opt in ('--help', '-h'):
            usage()
        elif opt in ('--head',):
            heads.append(val)
        elif opt in ('--zone', '-Z'):
            zone = co.DnsZone(val)
            int(zone) # Triggers error if missing
        elif opt in ('--mask', '-m'):
            mask = val
        elif opt in ('--mask6', '-n'):
            mask6 = val
        elif opt in ('--dir', '-d'):
            data_dir = val
        elif opt in ('--comments',):
            with_comments = True
        elif opt in ('--build', '-b'):
            if not heads:
                print "Missing --head, required before build"
                usage(1)
            fm = ForwardMap(zone)
            if data_dir:
                fm.generate_zone_file(val, heads, data_dir)
            else:
                fm.generate_zone_file(val, heads, os.path.dirname(val))
        elif opt in ('--reverse', '-r'):
            if not (heads and mask):
                print "Missing --head and --mask, required before reverse build"
                usage(1)
            rm = ReverseMap(mask)
            if data_dir:
                rm.generate_reverse_file(val, heads, data_dir)
            else:
                rm.generate_reverse_file(val, heads, os.path.dirname(val))
        elif opt in ('--reverse6', '-s'):
            if not (heads and mask6):
                print "Missing --head and --mask6, required before reverse build"
                usage(1)
            rm = IPv6ReverseMap(mask6)
            if data_dir:
                rm.generate_reverse_file(val, heads, data_dir)
            else:
                rm.generate_reverse_file(val, heads, os.path.dirname(val))
        elif opt in ('--hosts', ):
            hf = HostsFile(zone)
            hf.generate_hosts_file(val, with_comments=with_comments)
        elif opt in ('-R'):
            heads = []


if __name__ == '__main__':
    main()
