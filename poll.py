import operator
import pdb
import os

import pykube
import etcd
from apscheduler.schedulers.blocking import BlockingScheduler

KUBE_CONFIG = os.environ.get("KUBE_CONFIG") or "/home/user/.kube/config"
ETCD_HOST = os.environ.get("ETCD_HOST") or "etcd1"
ETCD_PORT = os.environ.get("ETCD_PORT") or 2379
KUBE_NAMESPACE = os.environ.get("KUBE_NAMESPACE") or "default"
POLL_INTERVAL = os.environ.get("POLL_INTERVAL") or 10

#pdb.set_trace()

def parse_args():
    import argparse

    parser = argparse.ArgumentParser(description = "Periodically checks kubernetes LB status")
    parser.add_argument('-k', default = False, action = 'store_true')
    args = parser.parse_args()
    return args

def query_kube_api():
    global api
    svc_list = []

    svc = pykube.Service.objects(api).filter(namespace=KUBE_NAMESPACE)
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
    pods = pykube.Pod.objects(api).filter(namespace=KUBE_NAMESPACE)
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


def main():
    
    args = parse_args()
    client = etcd.Client(host=ETCD_HOST,port=ETCD_PORT,allow_reconnect=True)

    global api
    api = pykube.HTTPClient(pykube.KubeConfig.from_file(KUBE_CONFIG))
    # disable tls verification
    api.session.verify = args.k

    sched = BlockingScheduler()
    sched.add_job(query_kube_api, 'interval', seconds=POLL_INTERVAL)
    
    print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))
    try:
       sched.start()
    except (KeyboardInterrupt, SystemExit):
       pass

if __name__ == '__main__':
   main()


