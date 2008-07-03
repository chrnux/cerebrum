from ceresync import config
from ceresync import errors
import SpineClient
from popen2 import popen3
import unittest

class Sync:
    def __init__(self, incr=False, id=-1, auth_type=None):
        self.incr=incr
        self.auth_type= auth_type or config.conf.get('sync','auth_type')
        connection = SpineClient.SpineClient(config=config.conf,
                                             logger=config.logger).connect()
        import SpineCore
        try:
            self.session = connection.login(config.conf.get('spine', 'login'),
                                            config.conf.get('spine', 'password'))
        except SpineCore.Spine.LoginError, e:
            raise errors.LoginError(e)

        self.tr = self.session.new_transaction()
        self.cmd = self.tr.get_commands()
        self.view = self.tr.get_view()
        account_spread=config.conf.get('sync', 'account_spread')
        group_spread=config.conf.get('sync', 'group_spread')
        
        self.view.set_account_spread(self.tr.get_spread(account_spread))
        self.view.set_group_spread(self.tr.get_spread(group_spread))
        self.view.set_authentication_method(self.tr.get_authentication_type(self.auth_type))
        self.view.set_changelog(id)

    def __del__(self):
        try:
            for i in self.session.get_transactions():
                try: i.rollback()
                except: pass
        except: pass
        try: self.session.logout()
        except: pass

    def set_authtype(self, auth_type):
        self.auth_type = auth_type
        self.view.set_authentication_method(self.tr.get_authentication_type(auth_type))

    def _do_get(self, objtype, incr):
        if incr is None:
            incr=self.incr
        if incr:
            m = "get_%ss_cl" % objtype
        else:
            m = "get_%ss" % objtype
        res=[]
        for obj in getattr(self.view, m)():
            obj.type=objtype
            config.apply_override(obj, objtype)
            config.apply_default(obj, obj.type)
            config.apply_quarantine(obj, obj.type)
            res.append(obj)
        return res
    
    def get_accounts(self, incr=None):
        return self._do_get("account", incr)
        
    def get_groups(self, incr=None):
        return self._do_get("group", incr)

    def get_persons(self, incr=None):
        return self._do_get("person", incr)        

    def get_ous(self, incr=None):
        return self._do_get("ou", incr)
    
    def close(self):
        self.tr.commit()
        self.session.logout()

class Pgp:
    def __init__(self, pgp_prog=None, enc_opts='', dec_opts='', keyid=None):
        # Handle NoOptionError?
        pgp_prog= pgp_prog or config.conf.get('pgp', 'prog')
        enc_opts= enc_opts or config.conf.get('pgp', 'encrypt_opts')
        dec_opts= dec_opts or config.conf.get('pgp', 'decrypt_opts')
        keyid= keyid or config.conf.get('pgp', 'keyid')

        self.pgp_enc_cmd= [ pgp_prog,
            '--recipient', keyid,
            '--default-key', keyid,
        ] + enc_opts.split()
        self.pgp_dec_cmd= [pgp_prog] + dec_opts.split()
    
    def decrypt(self, cryptstring):
        message= cryptstring
        if cryptstring:
            fin,fout,ferr= popen3(' '.join(self.pgp_dec_cmd))
            fout.write(cryptstring)
            fout.close()
            message= fin.read()
            fin.close()
            ferr.close()
        return message

    def encrypt(self, message):
        fin,fout,ferr= popen3(' '.join(self.pgp_enc_cmd))
        fout.write(message)
        fout.close()
        cryptstring= fin.read()
        fin.close()
        ferr.close()
        return cryptstring

class PgpTestCase(unittest.TestCase):
    def setUp(self):
        self.p= Pgp()
        self.message= 'FooX123.-=/'

    def testEncrypt(self):
        e= self.p.encrypt(self.message).strip()
        assert e.startswith('-----BEGIN PGP MESSAGE-----') and \
            e.endswith('-----END PGP MESSAGE-----')

    def testEncryptDecrypt(self):
        cryptstring= self.p.encrypt(self.message)
        assert self.message == self.p.decrypt(cryptstring), \
                'encryption and decryption yield wrong result'

if __name__ == '__main__':
    unittest.main()
