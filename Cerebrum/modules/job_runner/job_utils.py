# -*- coding: iso-8859-1 -*-

# Copyright 2004 University of Oslo, Norway
#
# This file is part of Cerebrum.
#
# Cerebrum is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Cerebrum is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Cerebrum; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import time
import socket
import signal
import os
import threading

import cereconf
from Cerebrum import Errors

class When(object):
    def __init__(self, freq=None, time=None):
        """Indicates that a job should be ran either with a specified
        frequency, or at the specified time"""
        assert freq is not None or time is not None
        assert not (freq is not None and time is not None)
        self.freq = freq
        self.time = time

        # TODO: support not-run interval to prevent running jobs when
        # FS is down etc.
        
    def next_delta(self, last_time, current_time):
        """Returns # seconds til the next time this job should run
        """
        if self.freq is not None:
            return last_time + self.freq - current_time
        else:
            times = []
            for t in self.time:
                d = t.next_time(last_time)
                times.append(d + last_time - current_time)
            return min(times)

    def __str__(self):
        if self.time:
            return "time=(%s)" % ",".join([str(t) for t in self.time])
        return "freq=%s" % time.strftime('%H:%M.%S',
                                         time.gmtime(self.freq))

class Time(object):
    def __init__(self, min=None, hour=None, wday=None, max_freq=None):
        """Emulate time part of crontab(5), None=*

        When using Action.max_freq of X hours and a Time object for a
        specific time each day, the Action.max_freq setting may delay
        a job so that a job that should be ran at night is ran during
        daytime (provided that something has made the job ran at an
        unusual hour earlier).

        To avoid this, set Time.max_freq.  This prevents next_time
        from checking wheter the job should have started until
        last_time+max_freq has passed.  I.e. if max_freq=1 hour the
        job is set to run at 12:30, but was ran at 12:00, the job will
        not run until the next matching time after 13:00.  If the
        Action.max_freq had been used, the job would have ran at
        13:00."""

        # TBD: what mechanisms should be provided to prevent new jobs
        # from being ran immeadeately when the time is not currently
        # within the correct range?

        self.min = min
        if min is not None:
            self.min.sort()
        self.hour = hour
        if hour is not None:
            self.hour.sort()
        self.wday = wday
        if wday is not None:
            self.wday.sort()
        self.max_freq = max_freq or 0

    def _next_list_value(self, val, list, size):
        for n in list:
            if n > val:
                return n, 0
        return min(list), 1

    def delta_to_leave(self, t):
        """Return a very rough estimate of the number of seconds until
        we leave the time-period covered by this Time object"""
        
        hour, min, sec, wday = (time.localtime(t))[3:7]
        if self.wday is not None and wday in self.wday:
            return 3600*24 - (sec+min*60+hour*3600)
        if self.hour is not None and hour in self.hour:
            return (60-min)*60
        if self.min is not None and min in self.min:
            return 60 - sec

    def next_time(self, prev_time):
        """Return the number of seconds until next time after num"""
        hour, min, sec, wday = (time.localtime(prev_time+self.max_freq))[3:7]

        add_week = 0
        for i in range(10):
            if self.wday is not None and wday not in self.wday:
                # finn midnatt neste ukedag
                hour = 0
                min = 0
                t, wrap = self._next_list_value(wday, self.wday, 6)
                wday = t
                if wrap:
                    add_week = 1

            if self.hour is not None and hour not in self.hour:
                # finn neste time, evt neste ukedag
                min = 0
                t, wrap = self._next_list_value(hour, self.hour, 23)
                hour = t
                if wrap:
                    wday += 1
                    continue

            if self.min is not None and min not in self.min:
                # finn neste minutt, evt neste ukedag
                t, wrap = self._next_list_value(min, self.min, 59)
                min = t
                if wrap:
                    hour += 1
                    continue

            # Now calculate the diff
            old_hour, old_min, old_sec, old_wday = (time.localtime(prev_time))[3:7]
            week_start_delta = (old_wday*24*3600 + old_hour*3600 + old_min*60 + old_sec)

            ret = add_week*7*24*3600 + wday*24*3600 + hour*3600 + min*60 - week_start_delta

            # Assert that the time we find is after the previous time
            if ret <= 0:
                if self.min is not None:
                    min += 1
                elif self.hour is not None:
                    hour += 1
                elif self.wday is not None:
                    wday += 1
                continue
            return ret
        raise ValueError, "Programming error for %i" % prev_time

    def __str__(self):
        ret = []
        if self.wday:
            ret.append("wday="+":".join(["%i" % w for w in self.wday]))
        if self.hour:
            ret.append("h="+":".join(["%i" % w for w in self.hour]))
        if self.min:
            ret.append("m="+":".join(["%i" % w for w in self.min]))
        return ",".join(ret)
    
class SocketHandling(object):
    """Simple class for handling client and server communication to
    job_runner"""

    class Timeout(Exception):
        """Raised by send_cmd() to interrupt a hanging socket call"""
    
    def timeout(sig, frame) :
        raise SocketHandling.Timeout("Timeout")
    timeout = staticmethod(timeout)

    def __init__(self, logger):
        self._is_listening = False
        signal.signal(signal.SIGALRM, SocketHandling.timeout)
        self.logger = logger

    def _format_time(self, t):
        if t:
            return time.asctime(time.localtime(t))
        return None

    def _show_job(self, jobname, job_runner):
        job = job_runner.job_queue.get_known_jobs().get(
            jobname, None)
        if not job:
            return 'Unknown job %s' % jobname

        tmp = self._format_time(job_runner.job_queue._started_at.get(jobname))
        if tmp:
            ret = "Status: running, started at %s\n" % tmp
        else:
            tmp = self._format_time(job_runner.job_queue._last_run.get(jobname))
            ret = "Status: not running.  Last run: %s\n" % tmp or 'unknown'
            ret += "Last exit status: %s\n" % job.last_exit_msg
        ret += "Command: %s\n" % job.get_pretty_cmd()
        ret += "Pre-jobs: %s\n" % job.pre
        ret += "Post-jobs: %s\n" % job.post
        ret += "Non-concurrent jobs: %s\n" % job.nonconcurrent
        ret += "When: %s, max-freq: %s\n" % (job.when, job.max_freq)
        if job.max_duration is not None:
            ret += "Max duration: %s minutes\n" % (job.max_duration/60)
        else:
            ret += "Max duration: %s\n" % (job.max_duration)
        return ret
        
        
    def start_listener(self, job_runner):
        self.socket = socket.socket(socket.AF_UNIX)
        self.socket.bind(cereconf.JOB_RUNNER_SOCKET)
        self.socket.listen(1)
        self._is_listening = True
        while True:
            try:
                conn, addr = self.socket.accept()
            except socket.error:
                # "Interrupted system call" May happen occasionaly, Try again
                time.sleep(1)
                continue
            while 1:
                data = conn.recv(1024).strip()
                if data == 'RELOAD':
                    job_runner.job_queue.reload_scheduled_jobs()
                    job_runner.wake_runner_signal()
                    self.send_response(conn, 'OK')
                    break
                elif data == 'QUIT':
                    job_runner.ready_to_run = ('quit',)
                    self.send_response(
                        conn, 'QUIT is now only entry in ready-to-run queue')
                    job_runner.quit()
                    break
                elif data == 'KILL':
                    job_runner.queue_paused_at = time.time()
                    job_runner.ready_to_run = ()
                    self.send_response(
                        conn, 'Initiating shutdown')
                    job_runner.quit()
                    break
                elif data == 'PAUSE':
                    job_runner.queue_paused_at = time.time()
                    self.send_response(conn, 'OK')
                    break
                elif data == 'RESUME':
                    job_runner.queue_paused_at = 0
                    job_runner.wake_runner_signal()
                    self.send_response(conn, 'OK')
                    break
                elif data.startswith('RUNJOB '):
                    jobname, with_deps = data[7:].split()
                    with_deps=int(with_deps)
                    if not job_runner.job_queue.get_known_jobs().has_key(jobname):
                        self.send_response(conn, 'Unknown job %s' % jobname)
                    else:
                        if with_deps:
                            job_runner.job_queue.insert_job(
                                job_runner.job_queue._run_queue, jobname)
                            self.send_response(
                                conn, 'Added %s to queue with dependencies' % jobname)
                        else:
                            job_runner.job_queue.get_forced_run_queue().append(jobname)
                            self.send_response(
                                conn, 'Added %s to head of queue' % jobname)
                        job_runner.wake_runner_signal()
                    break
                elif data.startswith('SHOWJOB '):
                    self.send_response(conn, self._show_job(data[8:], job_runner))
                    break
                elif data == 'STATUS':
                    ret = "Run-queue: \n  %s\n" % "\n  ".join(
                        [str({'name': x['name'], 'pid': x['pid'],
                              'started': time.strftime(
                        '%H:%M.%S', time.localtime(x['started']))})
                         for x in job_runner.job_queue.get_running_jobs()])

                    
                    ret += 'Ready jobs: \n  %s\n' % "\n  ".join(
                        [str(x) for x in job_runner.job_queue.get_run_queue()])
                    ret += 'Threads: \n  %s' % "\n  ".join(
                        [str(x) for x in threading.enumerate()])
                    tmp = job_runner.job_queue.get_known_jobs().keys()
                    tmp.sort()
                    ret += '\n%-35s %s\n' % ('Known jobs', '  Last run  Last duration')
                    for k in tmp:
                        t2 = job_runner.job_queue._last_run[k]
                        human_part = ""
                        if t2:
                            human_part = " (" + time.strftime("%F %T", time.localtime(t2)) + ")"
                        self.logger.debug("Last run of '%s' is '%s'%s" %
                                          (k, t2, human_part))
                        if t2:
                            t = time.strftime('%H:%M.%S', time.localtime(t2))
                            days = int((time.time()-t2)/(3600*24))
                        else:
                            t = 'unknown '
                            days = 0
                        t2 = job_runner.job_queue._last_duration[k]
                        if t2:
                            t += '  '+time.strftime('%H:%M.%S', time.gmtime(t2))
                        else:
                            t += '  unknown'
                        if days:
                            t += " (%i days ago)" % days
                        ret += "  %-35s %s\n" % (k, t)
                    if job_runner.sleep_to:
                        ret += 'Sleep to %s (%i seconds)\n' % (
                            time.strftime('%H:%M.%S', time.localtime(job_runner.sleep_to)),
                            job_runner.sleep_to - time.time())
                    if job_runner.queue_paused_at:
                        ret += "Notice: Queue paused for %s hours\n" % (
                            time.strftime(
                            '%H:%M.%S', time.gmtime(time.time() - job_runner.queue_paused_at)))
                    self.send_response(conn, ret)
                    break
                elif data == 'PING':
                    self.send_response(conn, 'PONG')
                    break
                else:
                    print "Unkown command: %s" % data
                if not data: break
            conn.close()    

    def ping_server(self):
        try:
            os.stat(cereconf.JOB_RUNNER_SOCKET)
            if self.send_cmd("PING") == 'PONG':
                return 1
        except socket.error:   # No server seems to be running
            print "WARNING: Removing stale socket"
            os.unlink(cereconf.JOB_RUNNER_SOCKET)
            pass
        except OSError:        # File didn't exist
            pass
        return 0

    def send_response(self, sock, msg):
        """Send response, including .\n response terminator"""
        if msg == ".\n":
            msg = "..\n"
        msg = msg.replace("\n.\n", "\n..\n")
        sock.send("%s\n.\n" % msg)

    def send_cmd(self, cmd, timeout=2):
        """
        Send command, decode and return response.
        Raises SocketHandling.Timeout if no response has come
        in timeout seconds.
        """
        signal.alarm(timeout)
        try:
            self.socket = socket.socket(socket.AF_UNIX)
            self.socket.connect(cereconf.JOB_RUNNER_SOCKET)
            self.socket.send("%s\n" % cmd)

            ret = ''
            while 1:
                tmp = self.socket.recv(1024)
                if not tmp:
                    break
                if tmp == ".\n" or tmp.find("\n.\n") != -1:
                    tmp = tmp.replace("\n..\n", "\n.\n")
                    ret += tmp[:-2]
                    break
                ret += tmp.replace("\n..\n", "\n.\n")
            ret = ret.strip()
            self.socket.close()
        except:
            signal.alarm(0)
            raise
        signal.alarm(0)
        return ret

    def cleanup(self):
        if not self._is_listening:
            return
        try:
            os.unlink(cereconf.JOB_RUNNER_SOCKET)
        except OSError:
            pass

    def __del__(self):
        self.cleanup()

class DbQueueHandler(object):
    def __init__(self, db, logger):
        self.db = db
        self.logger = logger

    def get_last_run(self):
        ret = {}
        for r in self.db.query(
            """SELECT id, timestamp
            FROM [:table schema=cerebrum name=job_ran]"""):
            ret[r['id']] = r['timestamp'].ticks()
        self.logger.debug("get_last_run: %s" % ret)
        return ret

    def update_last_run(self, id, timestamp):
        timestamp = self.db.TimestampFromTicks(int(timestamp))
        self.logger.debug("update_last_run(%s, %s)" % (id, timestamp))

        try:
            self.db.query_1("""
            SELECT 'yes' AS yes
            FROM [:table schema=cerebrum name=job_ran]
            WHERE id=:id""", locals())
        except Errors.NotFoundError:
            self.db.execute("""
            INSERT INTO [:table schema=cerebrum name=job_ran]
            (id, timestamp)
            VALUES (:id, :timestamp)""", locals())
        else:
            self.db.execute("""UPDATE [:table schema=cerebrum name=job_ran]
            SET timestamp=:timestamp
            WHERE id=:id""", locals())
        self.db.commit()

    
class JobQueue(object):
    """Handles the job-queuing in job_runner.

    Supports detecion of jobs that are independent of other jobs in
    the ready-to-run queue.  A job is independent if no pre/post jobs
    for the job exists in the queue.  This check is done recursively.
    Note that the order of pre/post entries for job does not indicate
    a dependency.
    """

    def __init__(self, scheduled_jobs, db, logger, debug_time=0):
        """Initialize the JobQueue.
        - scheduled_jobs is a reference to the module implementing
          get_jobs()
        - debug_time is number of seconds to increase current-time
          with for each call to get_next_job_time().  Default is to
          use the system-clock"""
        self._scheduled_jobs = scheduled_jobs 
        self.logger = logger
        self._known_jobs = {}
        self._run_queue = []
        self._running_jobs = []
        self._last_run = {}
        self._started_at = {}
        self._last_duration = {}         # For statistics in --status
        self.db_qh = DbQueueHandler(db, logger)
        self._debug_time=debug_time
        self.reload_scheduled_jobs()
        self._forced_run_queue = []
        
    def reload_scheduled_jobs(self):
        reload(self._scheduled_jobs)
        old_jobnames = self._known_jobs.keys()
        new_jobnames = []
        for job_name, job_action in self._scheduled_jobs.get_jobs().items():
            self._add_known_job(job_name, job_action)
            new_jobnames.append(job_name)
        for n in old_jobnames:
            if n not in new_jobnames:
                del(self._known_jobs[n])
        # Also check if last_run values has been changed in the DB (we
        # don't bother with locking the update to the dict)
        for k, v in self.db_qh.get_last_run().items():
            self._last_run[k] = v

    def get_known_job(self, job_name):
        return self._known_jobs[job_name]
    
    def get_known_jobs(self):
        return self._known_jobs
    
    def _add_known_job(self, job_name, job_action):
        """Adds job to list of known jobs, preserving
        state-information if we already know about the job"""
        if job_action.call:
            job_action.call.set_logger(self.logger)
            job_action.call.set_id(job_name)
        if self._known_jobs.has_key(job_name):  # Preserve info when reloading
            job_action.copy_runtime_params(self._known_jobs[job_name])
        self._known_jobs[job_name] = job_action
        # By setting _last_run to the current time we prevent jobs
        # with a time-based When from being ran imeadeately (note that
        # reload_scheduled_jobs will overwrite this value if an entry
        # exists in the db)
        if job_action.when and job_action.when.time:
            self._last_run[job_name] = time.time()
        else:
            self._last_run[job_name] = 0
        self._last_duration[job_name] = 0

    def has_queued_prerequisite(self, job_name, depth=0):
        """Recursively check if job_name has a pre-requisite in run_queue."""

        # TBD: if a multi_ok=1 job has pre/post dependencies, it could
        # be delayed so that the same job is executed several times,
        # example (conver_ypmap is a post-job for both generate jobs):
        # ['generate_group', 'convert_ypmap', 'generate_passwd', 'convert_ypmap']
        # Is this a problem.  If so, how do we handle it?

        #self.logger.debug2("%shas_queued_prerequisite %s (%s) %s" % (
        #    "  " * depth, job_name, self._run_queue, self._running_jobs))

        # If a pre or post job of the main job is in the queue
        if depth > 0 and job_name in self._run_queue:
            return True
        # Job is currently running
        if job_name in [x[0] for x in self._running_jobs]:
            return True
        # Check any pre jobs for queue existence
        for tmp_name in self._known_jobs[job_name].pre:
            if self.has_queued_prerequisite(tmp_name, depth+1):
                return True
        # Check any post-jobs (except at depth=0, where the post-jobs
        # should be executed after us)
        if depth > 0:
            for tmp_name in self._known_jobs[job_name].post:
                if self.has_queued_prerequisite(tmp_name, depth+1):
                    return True
        else:
            # Check if any jobs in the queue has the main-job as a post-job.
            for tmp_name in self._run_queue:
                if job_name in self._known_jobs[tmp_name].post:
                    return True
            # any running jobs which has main-job as post-job
            for tmp_name in [x[0] for x in self._running_jobs]:
                if job_name in self._known_jobs[tmp_name].post:
                    return True
        return False

    def get_running_jobs(self):
        return [ {'name': x[0],
                  'pid': x[1],
                  'call': (self._known_jobs.has_key(x[0]) and
                           self._known_jobs[x[0]].call or None),
                  'started': self._started_at[x[0]]} for x in self._running_jobs ]

    def kill_running_jobs(self, sig=signal.SIGTERM):
        """Send signal to all running jobs"""
        for i in self._running_jobs:
            try:
                os.kill(i[1], sig)
            except OSError, e:
                # Job have already quitted
                pass

    def job_started(self, job_name, pid, force=False):
        self._running_jobs.append((job_name, pid))
        self._started_at[job_name] = time.time()
        if force:
            self._forced_run_queue.remove(job_name)
        else:
            self._run_queue.remove(job_name)
        self.logger.debug("Started [%s]" % job_name)

    def job_done(self, job_name, pid, force=False):
        if pid is not None:
            self._running_jobs.remove((job_name, pid))

        if self._started_at.has_key(job_name):
            self._last_duration[job_name] = (
                time.time() - self._started_at[job_name])
            self.logger.debug("Completed [%s/%i] after %f seconds" % (
                job_name,  pid or -1, self._last_duration[job_name]))
        else:
            if force:
                self._forced_run_queue.remove(job_name)
            else:
                self._run_queue.remove(job_name)
            self.logger.debug("Completed [%s/%i] (start not set)" % (
                job_name,  pid or -1))
        if not (self._known_jobs.has_key(job_name)):   # due to reload of config
            logger.debug("Completed unknown job %s" % job_name)
            return
        if (pid is None or
            (self._known_jobs[job_name].call and
             self._known_jobs[job_name].call.wait)):
            self._last_run[job_name] = time.time()
            self.db_qh.update_last_run(job_name, self._last_run[job_name])
        else:
            # This means that an assertRunning job has terminated.
            # Don't update last_run as this would delay an attempt to
            # restart the job.
            pass

    def get_forced_run_queue(self):
        return self._forced_run_queue

    def get_run_queue(self):
        return self._run_queue
        
    def get_next_job_time(self, append=False):
        """find job that should be run due to the current time, or
        being a pre-requisit of a ready job.  Returns number of
        seconds to next event, and stores the queue internally."""

        global current_time
        jobs = self._known_jobs
        if append:
            queue = self._run_queue[:]
        else:
            queue = []
        if self._debug_time:
            current_time += self._debug_time
        else:
            current_time = time.time()
        min_delta = 999999
        for job_name in jobs.keys():
            next_delta = jobs[job_name].next_delta(self._last_run[job_name],
                                                   current_time)
            if next_delta is None:
                continue
            if append and job_name in self._run_queue:
                # Without this, a previously added job that has a
                # pre/post job with multi_ok=True would get the
                # pre/post job appended once each time
                # get_next_job_time was called.
                continue

            # TODO: vent med � legge inn jobbene, slik at de som
            # har when=time kommer f�r de som har when=freq.                
            if next_delta <= 0:
                pre_len = len(queue)
                self.insert_job(queue, job_name)
                if pre_len == len(queue):
                    continue     # no jobs was added
            min_delta = min(next_delta, min_delta)
        self.logger.debug("Delta=%i, a=%i/%i Queue: %s" % (
            min_delta, append, len(self._run_queue), str(queue)))
        self._run_queue = queue
        return min_delta

    def insert_job(self, queue, job_name, already_checked=None):
        """Recursively add job and all its prerequisited jobs.

        We allways process all parents jobs, but they are only added to
        the queue if it won't violate max_freq."""

        if already_checked is None:
            already_checked = []
        if job_name in already_checked:
            self.logger.info("Attempted to add %s, but it is already in %s" % (job_name, already_checked))
            return
        already_checked.append(job_name)
        
        this_job = self._known_jobs[job_name]
        for j in this_job.pre or []:
            self.insert_job(queue, j, already_checked=already_checked)

        if job_name not in queue or this_job.multi_ok:
            if (this_job.max_freq is None or
                current_time - self._last_run[job_name] > this_job.max_freq):
                if job_name not in [x[0] for x in self._running_jobs]:
                    # Don't add to queue if job is currently running
                    queue.append(job_name)

        for j in this_job.post or []:
            self.insert_job(queue, j, already_checked=already_checked)


    def has_conflicting_jobs_running(self, job_name):
        """Finds out if there are any jobs running that conflict with
        the given job, as defined by the job's setup (via Action)

        Returns True if there are any such jobs, False otherwise

        """
        this_job = self._known_jobs[job_name]
        for potential_anti_job in [x[0] for x in self._running_jobs]:
            if potential_anti_job in this_job.nonconcurrent:
                # It's confirmed that there's at least one running job
                # that conflicts
                return True 
        return False 


    def dump_jobs(scheduled_jobs, details=0):
        jobs = scheduled_jobs.get_jobs()
        shown = {}

        def dump(name, indent):
            info = []
            if details > 0:
                if jobs[name].when:
                    info.append(str(jobs[name].when))
            if details > 1:
                if jobs[name].max_freq:
                    info.append("max_freq=%s" % time.strftime('%H:%M.%S',
                                                 time.gmtime(jobs[name].max_freq)))
            if details > 2:
                if jobs[name].pre:
                    info.append("pre="+str(jobs[name].pre))
                if jobs[name].post:
                    info.append("post="+str(jobs[name].post))
            print "%-40s %s" % ("   " * indent + name, ", ".join(info))
            shown[name] = True
            for k in jobs[name].pre or ():
                dump(k, indent + 2)
            for k in jobs[name].post or ():
                dump(k, indent + 2)
        keys = jobs.keys()
        keys.sort()
        for k in keys:
            if jobs[k].when is None:
                continue
            dump(k, 0)
        print "Never run: \n%s" % "\n".join(
            ["  %s" % k for k in jobs.keys() if not shown.has_key(k)])

    dump_jobs = staticmethod(dump_jobs)

def pretty_jobs_presenter(jobs, args):
    """Utility function to give a human readable presentation of the defined
    jobs. This should simulate job_runner's presentation, to be able to get the
    information in test, without having to run a real job_runner.

    To use the function, feed it with the jobs from a given scheduled_jobs.py.

    @type jobs: class Cerebrum.modules.job_runner.job_actions.Jobs
    @param jobs:
        A class with all the jobs to present. Normally the AllJobs class in a
        given scheduled_jobs.

    @type args: list
    @param args:
        Input arguments, typically sys.argv[1:]. This is to be able to present
        the jobs in different ways, without the need of much code in
        scheduled_jobs.py. Not implemented yet, but '--show-job' could for
        example be a candidate.

    """
    if not args:
        print "%d jobs defined" % len(jobs.get_jobs())
        return

    # Should we use getopt here?
    if '-l' in args:
        for name in sorted(jobs.get_jobs()):
            print name
    elif '--show-job' in args:
        try:
            jobname = args[args.index('--show-job') + 1]
        except IndexError:
            print "No jobname is given"
            return
        try:
            job = jobs.get_jobs()[jobname]
        except KeyError:
            print "No such job: %s" % jobname
            return
        print "Command: %s" % job.get_pretty_cmd()
        print "Pre-jobs: %s" % job.pre
        print "Post-jobs: %s" % job.post
        print "Non-concurrent jobs: %s" % job.nonconcurrent
        print "When: %s, max-freq: %s" % (job.when, job.max_freq)
    elif '--dump' in args:
        dumplevel = args[args.index('--dump') + 1]
        print "not implemented yet..."
    elif '-v' in args:
        for name, job in sorted(jobs.get_jobs().iteritems()):
            print "Job: %s:" % name
            print "  Command: %s" % job.get_pretty_cmd()
            if job.pre:
                print "  Pre-jobs: %s" % job.pre
            if job.post:
                print "  Post-jobs: %s" % job.post
            if job.nonconcurrent:
                print "  Non-concurrent jobs: %s" % job.nonconcurrent
            print "  When: %s, max-freq: %s" % (job.when, job.max_freq)
        #return ret
    else:
        print "--show-job JOBNAME   Show a given job"
        print "-l                   List all the jobs"
        print "-v                   List jobs verbosely"

def run_tests():
    def parse_time(t):
        return time.mktime(time.strptime(t, '%Y-%m-%d %H:%M')) + time.timezone
    def format_time(sec):
        # %w has a different definition of day 0 than the localtime
        # tuple :-(
        return time.strftime('%Y-%m-%d %H:%M', time.localtime(sec)) + \
               " w=%i" % (time.localtime(sec))[6]
    def format_duration(sec):
        return "%s %id" % (
            time.strftime('%H:%M', time.gmtime(abs(delta))), int(delta/(3600*24)))
    tests = [(When(time=[Time(wday=[5], hour=[5], min=[30])]),
              (('2004-06-10 17:00', '2004-06-14 20:00'),
               ('2004-06-11 17:00', '2004-06-14 20:00'),
               ('2004-06-12 17:00', '2004-06-14 20:00'),
              )),
             (When(time=[Time(wday=[5], hour=[5], min=[30], max_freq=24*60*60)]),
              (('2004-06-10 17:00', '2004-06-14 20:00'),
               ('2004-06-11 17:00', '2004-06-14 20:00'),
               ('2004-06-12 17:00', '2004-06-14 20:00'),
              )),
             (When(time=[Time(hour=[4], min=[5])]),
              (('2004-06-01 03:00', '2004-06-01 04:00'),
               ('2004-06-01 03:00', '2004-06-01 04:10'),
               ('2004-06-01 03:00', '2004-06-01 04:20'),
              ))]
    for when, times in tests:
        print "When obj: ", when
        for t in times:
            # convert times to seconds since epoch in localtime
            prev = parse_time(t[0])
            now = parse_time(t[1])
            delta = when.next_delta(prev, now)
            print "  prev=%s, now=%s -> %s [delta=%i/%s]" % (
                format_time(prev), format_time(now), 
                format_time(now+delta), delta, format_duration(delta))

if __name__ == '__main__':
    run_tests()

