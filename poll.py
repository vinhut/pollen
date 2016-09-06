import operator
import pykube
import etcd
import pdb
import os

KUBE_CONFIG="/home/user/.kube/config"

client = etcd.Client(host='etcd1',port=2379,allow_reconnect=True)
api = pykube.HTTPClient(pykube.KubeConfig.from_file(KUBE_CONFIG))
# disable tls verification
api.session.verify = False

#pdb.set_trace()

svc_list = []

svc = pykube.Service.objects(api).filter(namespace="default")
for b in svc:
   # service name
   svc_name = b.name
   if svc_name == 'kubernetes':
      continue
   svc_list.append(svc_name)
   # public port
   svc_port = b.obj['spec']['ports'][0]['port']
   # target port
   tgt_port = b.obj['spec']['ports'][0]['targetPort']
   client.write('/loadbalancer/kube/service/'+svc_name, '{"svc_port":'+str(svc_port)+', "tgt_port":'+str(tgt_port)+'}')

# clean removed service
directory = client.get("/loadbalancer/kube/service")
for svcname in directory.children:
    _,base = os.path.split(svcname.key)
    if not base in svc_list:
       client.delete(svcname.key)

# get all pods
pods = pykube.Pod.objects(api).filter(namespace="default")
# get only ready pod
ready_pods = filter(operator.attrgetter("ready"), pods)

pods_list = []

for i in ready_pods:
   # get pod name
   pod_name = i.obj['metadata']['name']
   pods_list.append(pod_name)
   # get pod service name
   svc_name = i.obj['metadata']['labels']['app']
   # print pod internal ip
   pod_ip = i.obj['status']['podIP']
   client.write('/loadbalancer/kube/pods/'+svc_name+'/'+pod_name, pod_ip)

# clean removed pods
for i in svc_list:
  directory = client.get('/loadbalancer/kube/pods/'+i)
  for podname in directory.children:
      _,base = os.path.split(podname.key)
      if not base in pods_list:
         client.delete(podname.key)
