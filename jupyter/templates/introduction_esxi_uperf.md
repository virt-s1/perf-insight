#### ESXi Network Performance Testing

VMware ESXi (formerly ESXi) is an enterprise-class, type-1 hypervisor developed by VMware for deploying and serving virtual computers.

VMware vSphere supports different types of network adapters, like VMXNET3 (v3 or v4), E1000E, E1000, PVRDMA, SR-IOV, etc. Here, we choose the VMXNET3 as our test target. From typical network performance test cases, normally, we (with pbench-uperf) test tcp_stream, tcp_maerts, udp_stream, tcp_rr, udp_rr with the default configuration. You can design from code or your configurations to test others' complex test cases.

#### Contact information

IRC: #virt-pt @irc.devel.redhat.com  
Mail list: virt-perftest@redhat.com

Project owner: Bo Yang <boyang@redhat.com>
