#### ESXi Network Performance Testing

VMware vSphere(Formerly ESXi) is an enterprise-class, type-1 hypervisor developed by VMware for deploying and serving virtual computers.

The ESXi supports different types of network adapters, like VMXNET3(v3 or v4), E1000E, E1000, PVRDMA, SR-IOV, etc. Here, choose the VMXNET3 as a network performance test target adapter.

For typical network performance test cases, we conduct TCP/UDP_STREAM, TCP/UDP_MAERTS, and TCP/UDP_RR tests with the pbench-uperf tool. Also, we offer "full", "default" and "lite" test suites to meet different test requirements.

**Test suites**

| Test suite | Time cost         |
| ---------- | ----------------- |
| lite       | 1.0 ~ 1.5 hours   |
| default    | 4.5 ~ 6.0 hours   |
| full       | 10.5 ~ 12.0 hours |

**Topologic**

```
------------------------------------------------------
|  ------------------            ------------------  |
|  |  uperf client  |    link    |  uperf server  |  |
|  |      VM 1      |  <------>  |      VM 2      |  |
|  ------------------            ------------------  |
|                                                    |
|                  Hypervisor - ESXi                 |
|                       Host 1                       |
------------------------------------------------------
```

#### Contact information

IRC: #virt-pt @irc.devel.redhat.com  
Mail: <virt-perftest@redhat.com>

Owner: Bo Yang <boyang@redhat.com>
