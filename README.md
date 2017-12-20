# uncompress

Ansible uncompress module. Uncompresses an file after (optionally) copying it from the local machine.

## Example

```yaml
- name: Uncompress foo.gz to /tmp/foo
  uncompress: src=foo.gz dest=/tmp/foo

- name: Uncompress a file that is already on the remote machine
  uncompress: src=/tmp/foo.xz dest=/usr/local/bin/foo copy=no

- name: Uncompress a file that needs to be downloaded
  uncompress: src=https://example.com/example.bz2 dest=/usr/local/bin/example copy=no
```

## Notes

* requires C(file)/C(xz) commands on target host
* requires gzip and bzip python modules
* can handle I(gzip), I(bzip2) and I(xz) compressed files
* detects type of compressed file automatically