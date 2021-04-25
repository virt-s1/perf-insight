## About Us

RHEL Performance Testing on Virtualization Platforms, Performance Team, Beijing VirtQE S1.
Homepage: https://docs.engineering.redhat.com/display/VIRTPT/Virt+PT+Home

### Our mission

Make RHEL performance competitive.

### Contact Information

- IRC channel: #virt-pt @irc.devel.redhat.com
- Mailing list: virt-perftest@redhat.com
- Project Lead: Charles Shih <cheshi@redhat.com>
- Direct Manager: Tina Mao <ymao@redhat.com>

### Product Owners

| Product | Function | Name                       | Email                                  |
| :------ | :------- | :------------------------- | :------------------------------------- |
| ESXi    | storage  | Lily Du                    | ldu@redhat.com                         |
| ESXi    | network  | Bo Yang                    | boyang@redhat.com                      |
| Hyper-V | storage  | Xuemin Li                  | xuli@redhat.com                        |
| Hyper-V | network  | Bo Yang / Huijuan Zhao     | boyang@redhat.com / huzhao@redhat.com  |
| AWS     | storage  | Charles Shih               | cheshi@redhat.com                      |
| AWS     | network  | Frank Liang / Charles Shih | xiliang@redhat.com / cheshi@redhat.com |
| Azure   | storage  | Yuxin Sun                  | yuxisun@redhat.com                     |
| Azure   | network  | Huijuan Zhao               | huzhao@redhat.com                      |
| Aliyun  | storage  | Charles Shih               | cheshi@redhat.com                      |
| Aliyun  | network  | Charles Shih               | cheshi@redhat.com                      |


## About this site

This site is a part of Perf-insight which is used to collect, display, query, and analyze performance results. We hope that historical records can better guide our testing and share testing status more friendly.

### Perf-insight and Perf-agent

Perf-insight (as known as the reporting system for performance testing) is a data visualization based on enhanced pbench data model and fully compatible with pbench test results. So that the raw data, test logs, KPI reports, and even ideas and insights can be easily shared with other stakeholders.

Source code: https://github.com/virt-s1/perf-insight

Perf-agent is a toolkit helps set up the pbench test environment on various platforms, conduct pbench tests and collect test logs. It provides input data used by Perf-insight.

Source code: https://github.com/virt-s1/perf-agent
