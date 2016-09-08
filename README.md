Pollen is python program that primary use is to be paired with confd and to dynamically changes load balancer(eg : haproxy/nginx) configuration when kubernetes services/pods updated. 
Pollen stored list of kubes services/pods in etcd, so you must have setup etcd as a requirement.

### Configuration
**KUBE_CONFIG** kubernetes cli config, default to "/home/user/.kube/config"

**ETCD_HOST** etcd host or ip address, default to "etcd1"

**ETCD_PORT** etcd port, default to 2379

**KUBE_NAMESPACE** kubernetes namespace, default to "default"

**POLL_INTERVAL** polling interval in seconds, default to 10

