# EKS Deployment Instructions

https://docs.aws.amazon.com/eks/latest/userguide/getting-started-eksctl.html
The following are done on MacOS

## Prerequisites
### Install AWS CLI
https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html

### Configure credentials
You can see the credentials on AWS IAM
As per https://github.com/weaveworks/eksctl/issues/204, it is recommended that you create a cluster on an admin account
```
$ aws configure
AWS Access Key ID [None]: blah
AWS Secret Access Key [None]: bleh
Default region name [None]: region-code
Default output format [None]: json
```

### Install eksctl
For mac, we use home brew

```
$ brew tap weaveworks/tap
$ brew install weaveworks/tap/eksctl
$ eksctl version
```
version should be at least 0.14.0

### Install kubectl
This is already installed via homebrew

## Create cluster
```
eksctl create cluster \
--name commonfund-tools \
--version 1.14 \
--region us-east-1 \
--nodegroup-name standard-workers \
--node-type t3.medium \
--nodes 1 \
--nodes-min 1 \
--nodes-max 1 \
--ssh-access \
--ssh-public-key ~/.ssh/id_rsa.pub \
--managed
```

## Set up dashboard

```
DOWNLOAD_URL=$(curl -Ls "https://api.github.com/repos/kubernetes-sigs/metrics-server/releases/latest" | jq -r .tarball_url)
DOWNLOAD_VERSION=$(grep -o '[^/v]*$' <<< $DOWNLOAD_URL)
curl -Ls $DOWNLOAD_URL -o metrics-server-$DOWNLOAD_VERSION.tar.gz
mkdir metrics-server-$DOWNLOAD_VERSION
tar -xzf metrics-server-$DOWNLOAD_VERSION.tar.gz --directory metrics-server-$DOWNLOAD_VERSION --strip-components 1
kubectl apply -f metrics-server-$DOWNLOAD_VERSION/deploy/1.8+/
```

view deployment
```
kubectl get deployment metrics-server -n kube-system
```

Deploy dashboard
```
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v1.10.1/src/deploy/recommended/kubernetes-dashboard.yaml
```

create eks-admin service account and cluster role binding
```
kubectl apply -f eks-admin-service-account.yaml
```

#### Connecting to the dashboard
Get your token using this command
```
kubectl -n kube-system describe secret $(kubectl -n kube-system get secret | grep eks-admin | awk '{print $1}')
```
```
kubectl proxy --port=8080 --address='0.0.0.0' --disable-filter=true &
```

Go to this url http://localhost:8080/api/v1/namespaces/kube-system/services/https:kubernetes-dashboard:/proxy/#!/login


## Installing sigcom

Create a namespace where we can install our stuff
```
kubectl create namespace commonfund-tools
```

### Installing generic sigcom
To install generic sigcom, we use instructions in https://github.com/MaayanLab/signature-commons/tree/env-refactor

See it running:
```
kubectl get services --namespace=commonfund-tools
```

### Installing cfde version of sigcom
The following instructions are for deployment of the commonfund-tools version of sigcom.

1. Clone the env-refactor repo:
```
git clone --recurse-submodules --branch env-refactor git@github.com:dcic/signature-commons.git
```
2. edit the docker-compose file:
  image: maayanlab/sigcom:latest -> image: maayanlab/sigcom-cfde:latest

3. edit variables on .env.example and run ```charts/build_helm_chart.sh```

4. install
```
helm install charts/signature-commons/v1 \
  --namespace commonfund-tools --generate-name \
  -f charts/signature-commons/v1/values.yaml
```
5. See it running:
```
kubectl get services --namespace=commonfund-tools
```

## Set up the ingress
We now have our k8 cluster running signature commons. But we can't access it yet outside. We now need to have a NodePort that will act as a loadbalancer for our cluster.

Setup nginx-ingress-controller
```
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/master/deploy/static/mandatory.yaml
```

Setup our ingress-nginx service
```
kubectl apply -f ingress-service.yaml
```
Note here that we set our nodeports to 30080. This exposes this nodeport to the outside world but we can't use it yet until we add access to it via security groups

1. On Amazon EC2 Go to security groups. Select the security group for the cluster
2. On the inbound tab add the ff
  - Type: Custom TCP Rule
    Protocol: TCP
    Port Range: 30080
    Source: 0.0.0.0/0

You can now access your website on <hostname>:30080/

But we do not want that ugly port in there!

Solution! Load balancer!

We use amazon's network load balancer for this. Unlike application load balancers, we can get static IPs using nlb.
1. On EC2 go to Load Balancers
2. Select Create Load Balancer
3. Choose Network Load Balancer
4. Add some fancy name like my-fancy-load-balancer
5. Make sure the scheme is forward facing
6. Add a TCP listener to port 80
7. Add a TLS listener to port 443 
8. For the availability zone, choose the vpc used by your cluster
9. select availability zones + subnet (make sure it is public)
10. For the IP, choose elastic IP instead of Assigned by AWS
  - You may have to generate elastic IP's via the elastic IP section of the EC2
11. Upload your certificates (this is unavailable if you skip 7)
  - AWS issues free certificates via ACM
12. Create a target group and set port to 30800
13. Select instances to register to the group (this is the instances of your k8 clusters)
14. Review then ok


# Some useful commands
Deleting a namespace. This effectively deletes everything in that namespace
```
kubectl delete namespaces commonfund-tools
```

getting pods/ services/ ingresses under a namespace
```
# Get pods under commonfund-tools
kubectl get pods --namespace=commonfund-tools
```

Execute a command in a pod
```
kubectl exec -it --namespace=commonfund-tools <pod name> -- npx typeorm migration:run
```

delete pod/ service/ ingress under a namespace
```
# Get pods under commonfund-tools
kubectl delete pod <identifier> --namespace=commonfund-tools
```

Getting releases via helm
```
helm list --namespace=commonfund-tools
```

Upgrade our installation
```
helm upgrade --namespace=commonfund-tools -f /path/to/values.yaml v1-1583352262 /path/to/signature-commons/charts/signature-commons/v1
```

Delete cluster
```
eksctl delete cluster --name=commonfund-tools
```