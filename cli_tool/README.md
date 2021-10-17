# Example

```bash
# List all TestRuns
picli testrun-list

# Inspect a specified TestRun
picli testrun-inspect --testrun-id fio_ESXi_PERF_RHEL_8.4.0_20210503.1_x86_64_BIOS_SCSI_quick_D210802T111807

# Load a TestRun from the staging area
picli testrun-load --testrun-id fio_ESXi_PERF_RHEL_8.4.0_20210503.1_x86_64_BIOS_SCSI_quick_D210802T111807

# Fetch a TestRun to the staging area
picli testrun-fetch --testrun-id fio_ESXi_PERF_RHEL_8.4.0_20210503.1_x86_64_BIOS_SCSI_quick_D210802T111807

# Delete a specified TestRun
picli testrun-delete --testrun-id fio_ESXi_PERF_RHEL_8.4.0_20210503.1_x86_64_BIOS_SCSI_quick_D210802T111807

# Import a TestRun from external pbench-server
picli testrun-delete --testrun-id fio_KVM_RHEL_8.3.0_x86_64_Import_External_Demo_D20200911T075413
picli testrun-import --testrun-id fio_KVM_RHEL_8.3.0_x86_64_Import_External_Demo_D20200911T075413 \
    --external-url http://pbench.perf.lab.eng.bos.redhat.com/results/ibm-x3650m5-09.lab.eng.pek2.redhat.com/fio__2020.09.12T09.30.19/ \
    --external-url http://pbench.perf.lab.eng.bos.redhat.com/results/ibm-x3650m5-09.lab.eng.pek2.redhat.com/fio__2020.09.12T09.33.17/ \
    --external-url http://pbench.perf.lab.eng.bos.redhat.com/results/ibm-x3650m5-09.lab.eng.pek2.redhat.com/fio__2020.09.12T09.59.36/ \
    --external-url http://pbench.perf.lab.eng.bos.redhat.com/results/ibm-x3650m5-09.lab.eng.pek2.redhat.com/fio__2020.09.14T06.36.01/ \
    --metadata-keypair guest-cpu=40 \
    --metadata-keypair guest-flavor=ibm-x3650m5-09 \
    --metadata-keypair guest-memory=64GB \
    --metadata-keypair hardware-disk-backend=virtio \
    --metadata-keypair hardware-disk-capacity=372.6G \
    --metadata-keypair hardware-disk-driver=nvme \
    --metadata-keypair hardware-disk-format=raw \
    --metadata-keypair hypervisor-cpu= \
    --metadata-keypair hypervisor-cpu_model="Intel(R) Xeon(R) CPU E5-2630 v4 @ 2.20GHz" \
    --metadata-keypair hypervisor-version= \
    --metadata-keypair os-branch=RHEL-8.3 \
    --metadata-keypair os-compose=RHEL-8.3.0 \
    --metadata-keypair os-kernel=4.18.0-234.el8.x86_64 \
    --metadata-keypair testrun-comments= \
    --metadata-keypair testrun-date=2020-09-12 \
    --metadata-keypair testrun-id=fio_KVM_RHEL_8.3.0_x86_64_Import_External_Demo_D20200911T075413 \
    --metadata-keypair testrun-platform=KVM \
    --metadata-keypair testrun-type=fio \
    --metadata-keypair tool-fio-version=fio-3.19-3.el8.x86_64

# List all benchmark reports
picli benchmark-list

# Create a benchmark report
picli benchmark-create --base-id fio_Azure_RHEL-8.4.0-20210503.1_x86_gen1_localssd_quick_D210508T163611 \
    --test-id fio_Azure_RHEL-8.5.0-20210706.n.0_x86_gen1_localssd_quick_D210706T234925

# Inspect a benchmark report
picli benchmark-inspect --report-id benchmark_fio_Azure_RHEL-8.5.0-20210706.n.0_x86_gen1_localssd_quick_D210706T234925_over_fio_Azure_RHEL-8.4.0-20210503.1_x86_gen1_localssd_quick_D210508T163611

# Delete a benchmark report
picli benchmark-delete --report-id benchmark_fio_Azure_RHEL-8.5.0-20210706.n.0_x86_gen1_localssd_quick_D210706T234925_over_fio_Azure_RHEL-8.4.0-20210503.1_x86_gen1_localssd_quick_D210508T163611

# List all Jupyter Labs
picli lab-list

# Create a Jupyter Lab
picli lab-create --username cheshi --password redhat

# Delete a Jupyter Lab
picli lab-delete --username cheshi --password redhat

# Lise all studies
picli study-list

# Start a study
picli study-start --report-id benchmark_fio_Azure_RHEL-8.5.0-20210706.n.0_x86_gen1_localssd_quick_D210706T234925_over_fio_Azure_RHEL-8.4.0-20210503.1_x86_gen1_localssd_quick_D210508T163611 --username cheshi --password redhat

# Stop a study
picli study-stop --report-id benchmark_fio_Azure_RHEL-8.5.0-20210706.n.0_x86_gen1_localssd_quick_D210706T234925_over_fio_Azure_RHEL-8.4.0-20210503.1_x86_gen1_localssd_quick_D210508T163611 --username cheshi --password redhat

```
