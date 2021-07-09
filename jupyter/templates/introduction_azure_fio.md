#### Azure Storage Performance Testing

Microsoft Azure, formerly known as Windows Azure, is Microsoft's public cloud computing platform.

Azure supports different storage types: [Data disk types](https://docs.microsoft.com/en-us/azure/virtual-machines/disks-types)

\* We only test the Temporary disk(Local SSD) which is the highest performance disk type.  The temporary disk performance depands on the VM size. We use the Standard_M128m VM size which has the highest performance. [M-series introduction](https://docs.microsoft.com/en-us/azure/virtual-machines/m-series)

\* The Temporary disk data in the chart is the Standard_M128m VM size.

| Detail | Temporary disk | Ultra disk | Premium SSD | Standard SSD | Standard HDD |
| ------ | -------------- | ---------- | ----------- | ------------ | ------------ |
|Disk type |Local SSD |SSD   |SSD   |SSD   |HDD   |
|Max throughput |1600 MB/s |2,000 MB/s    |900 MB/s   |750 MB/s   |500 MB/s   |
|Max IOPS   |250,000| 160,000    |20,000   |6,000   |2,000   |


#### Contact information

IRC: #virt-pt @irc.devel.redhat.com  
Mail list: virt-perftest@redhat.com

Project owner: Yuxin Sun <yuxisun@redhat.com>
