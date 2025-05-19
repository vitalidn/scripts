# SSH update to fix critical vulnerability

Here is simple bash script to fix [CVE-2024-6387](https://ubuntu.com/security/CVE-2024-6387) by updating packages

## Run

```bash
ansible -i inventories/slotomania/sm-preprod-aws.ini all -m script -a 'scripts/custom/ssh-cve-fix/ssh-update.sh' -K
```

As vulnerability only starts in ubuntu 22 and newer it will skip any older hosts, like ubuntu 20 or 18