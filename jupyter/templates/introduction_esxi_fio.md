#### ESXi Storage Performance Testing

VMware ESXi (formerly ESX) is an enterprise-class, type-1 hypervisor developed by VMware for deploying and serving virtual computers. 

VMware vSphere supports different types of storage architectures, storage types at the VM logical level include "thick eager zeroed disk", "thick lazy zeroed disk", "thin disk", now we just test "thick eager zeroed disk"; Storage types at the VM physical level include "LSI Logic Parallel", "LSI Logic SAS", "VMware Paravirtual (or PVSCSI)" and "NVMe", we barely test "PVSCSI" and "NVMe", others virtual controllers are also possible in a VM, such as "AHCI SATA" (introduced in vSphere 5.5), "IDE", and also "USB controllers", but usually for specific cases (for example "SATA" or "IDE" are usually used for virtual DVD drives).

#### Contact information

IRC: #virt-pt @irc.devel.redhat.com  
Mail list: virt-perftest@redhat.com

Project owner: Lily Du <ldu@redhat.com>
