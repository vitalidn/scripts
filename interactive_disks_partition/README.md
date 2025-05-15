# Interactive Disk Partitioning Script

This script provides an interactive way to partition multiple disks across multiple hosts in a consistent manner. It's particularly useful for system administrators who need to set up identical disk configurations across multiple servers.

## Features

- Interactive disk partitioning across multiple hosts
- Support for host ranges (e.g., host[1:5])
- Automatic SSH and sudo access verification
- Detailed logging of all operations
- Safety checks to prevent accidental system disk modifications
- Support for multiple partitions per disk
- Consistent partition sizing across all disks
- Backup of partition tables before modifications
- Color-coded output for better visibility
- Comprehensive error handling and cleanup

## Prerequisites

- SSH access to target hosts
- Sudo privileges on target hosts
- `sgdisk` and `gdisk` utilities installed on target hosts
- Basic understanding of disk partitioning concepts

## Usage

```bash
./interactive_disks_partition.sh
```

The script will:
1. Prompt for host(s) to partition
2. Verify SSH and sudo access
3. Display available disks
4. Allow selection of target disks
5. Ask for number of partitions per disk
6. Ask for partition size in GiB
7. Create partitions with consistent naming (data1, data2, etc.)

## Safety Features

- Prevents modification of system disks without explicit confirmation
- Warns about existing partitions before deletion
- Creates backup of partition tables
- Validates all inputs before execution
- Logs all operations for audit purposes

## Logging

- All operations are logged to a file named after the host (e.g., `hostname.log`)
- Logs include timestamps and operation details
- Both successful operations and errors are recorded

## Error Handling

- Comprehensive error checking at each step
- Automatic cleanup on script termination
- Clear error messages with color coding
- Graceful exit on user cancellation

## Notes

- The script requires sudo privileges on target hosts
- All partitions are created as Linux filesystem partitions (type 8300)
- Partition names follow the pattern "dataN" where N is the partition number
- The script supports partitioning up to 128 partitions per disk

## Example

Here's an example of running the script:

```bash
$ ./interactive_disks_partition.sh
Enter host(s) to partition (e.g., host1 or host[1:5]): host[1:3]

INFO: Starting disk partitioning for host: host1
Enter sudo password: ******
INFO: Access OK

Available disks:
----------------------------------
NAME    SIZE    TYPE    MOUNTPOINT
sda     500G    disk    /
sdb     2T      disk    
sdc     2T      disk    
----------------------------------

Enter disks to partition (space-separated, e.g. sda sdb) or 'N' to skip this host: sdb sdc

WARNING: Disk /dev/sdb already has partitions:
----------------------------------------------------------------
NAME    SIZE    TYPE    MOUNTPOINT
sdb1    1T      part    /data1
sdb2    1T      part    /data2
----------------------------------------------------------------
Do you want to proceed with new partitioning? This will delete all existing partitions! (y/N): y

Enter number of partitions per disk (1-128): 4
Enter partition size in GiB: 500

INFO: Creating partition 1 on /dev/sdb (500GiB)
INFO: Creating partition 2 on /dev/sdb (500GiB)
INFO: Creating partition 3 on /dev/sdb (500GiB)
INFO: Creating partition 4 on /dev/sdb (500GiB)
INFO: Verified partitions on /dev/sdb

INFO: Creating partition 1 on /dev/sdc (500GiB)
INFO: Creating partition 2 on /dev/sdc (500GiB)
INFO: Creating partition 3 on /dev/sdc (500GiB)
INFO: Creating partition 4 on /dev/sdc (500GiB)
INFO: Verified partitions on /dev/sdc

Final disk layout:
----------------------------------
NAME    SIZE    TYPE    MOUNTPOINT
sda     500G    disk    /
sdb     2T      disk    
├─sdb1  500G    part    
├─sdb2  500G    part    
├─sdb3  500G    part    
└─sdb4  500G    part    
sdc     2T      disk    
├─sdc1  500G    part    
├─sdc2  500G    part    
├─sdc3  500G    part    
└─sdc4  500G    part    
----------------------------------
scsi-222273545002ee4ac -> ../../sda
scsi-222273545002ee4ac-part1 -> ../../sda1
scsi-222273545002ee4ac-part10 -> ../../sda10
scsi-222273545002ee4ac-part11 -> ../../sda11
.......


INFO: Starting disk partitioning for host: host2
[... similar process for host2 ...]

INFO: Starting disk partitioning for host: host3
[... similar process for host3 ...]
```

The script will create identical partitions on all specified disks across all hosts. In this example:
- 3 hosts were specified using the range notation `host[1:3]`
- On each host, disks `sdb` and `sdc` were selected
- 4 partitions of 500GiB each were created on each disk
- The script handled existing partitions with a warning and confirmation
- All operations were logged to separate log files for each host
- The final disk layout shows the tree structure of created partitions 