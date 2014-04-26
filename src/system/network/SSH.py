'''
Created on Jul 15, 2011

@author: Giulio
'''
from system.network.ShellProxy import ShellProxy
from system.tools import execCmd, SSH_EXEC

class SSH(ShellProxy):
    
    def __init__(self, hostname, user='root'):
        # TODO: add port
        ShellProxy.__init__(self)
        self.login = user + '@' + hostname
                
        
    def shell(self, cmd, block=True):
        '''
        Execute a shell command.
        @param cmd: a shell command string
        @param block: block waits until the command is finished. On this case
        shell returns None       
        '''
        # TODO: what about shell=True?
        return execCmd(cmd, dest=self.login, wait=block, shell=False, mode=SSH_EXEC)
    
    
    def connected(self):
        # TODO: maybe ping the server?
        raise NotImplementedError

'''
Some ssh parameters that can be implemented on the future:
 -c cipher_spec
     Selects the cipher specification for encrypting the session.

     Protocol version 1 allows specification of a single cipher.  The
     supported values are "3des", "blowfish", and "des".  3des
     (triple-des) is an encrypt-decrypt-encrypt triple with three dif-
     ferent keys.  It is believed to be secure.     blowfish is a fast
     block cipher; it appears very secure and is much faster than
     3des.  des is only supported in the ssh client for interoperabil-
     ity with legacy protocol 1 implementations that do not support
     the 3des cipher.  Its use is strongly discouraged due to crypto-
     graphic weaknesses.  The default is "3des".

     For protocol version 2, cipher_spec is a comma-separated list of
     ciphers listed in order of preference.  The supported ciphers
     are: 3des-cbc, aes128-cbc, aes192-cbc, aes256-cbc, aes128-ctr,
     aes192-ctr, aes256-ctr, arcfour128, arcfour256, arcfour, blow-
     fish-cbc, and cast128-cbc.     The default is:

       aes128-cbc,3des-cbc,blowfish-cbc,cast128-cbc,arcfour128,
       arcfour256,arcfour,aes192-cbc,aes256-cbc,aes128-ctr,
       aes192-ctr,aes256-ctr

-n   Redirects stdin from /dev/null (actually, prevents reading from
     stdin).  This must be used when ssh is run in the background.  A
     common trick is to use this to run X11 programs on a remote
     machine.  For example, ssh -n shadows.cs.hut.fi emacs & will
     start an emacs on shadows.cs.hut.fi, and the X11 connection will
     be automatically forwarded over an encrypted channel.  The ssh
     program will be put in the background.  (This does not work if
     ssh needs to ask for a password or passphrase; see also the -f
     option.)

-p port
     Port to connect to on the remote host.  This can be specified on
     a per-host basis in the configuration file.
'''