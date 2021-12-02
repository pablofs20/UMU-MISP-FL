# FL-trained ML models using real-time MISP data

## Overview
This demo aims to leverage the data coming from a MISP server and train a ML model from it using Federated Learning (FL). The main objective is to provide an alternative
method for an organization to use the IoCs shared through MISP and give a feedback. Once enough data has been received by the client, a FL process is triggered along with
an aggregator and some other clients, and a final model, trained collaboratively by all of the clients and their private data, is obtained. This resulting model is fed
back to the local MISP server and, therefore, it can be used by other involved organizations to deploy it in, e.g., an anomaly-based IDS.

For this experiment, we use several partitions of the [ToN-IoT dataset]{https://research.unsw.edu.au/projects/toniot-datasets}, one per configured client. Each partition (representing the data which would belong to an specific
organization) is used to feed the MISP server on one side (one event per dataset instance). On the other side, a MISP retriever module will periodically ask for new 
events and, once it has enough data, it will register against the FL aggregator that will be running from the beginning of the whole process. When the number of clients
connected to the aggregator is equal or higher than 2, the FL process will begin and a ML model will be trained collaboratively by the registered clients. Finally, this
model can be pushed back to the local MISP server to share it with other domains.

For the FL part, we leverage the Flower framework. Please consult the [official documentation]{https://flower.dev/docs/} for further details.

## Configuration
This software is coded and tested in Python 3.6.9. Since multiple libraries have been employed, we provide a Python requirements file containing all the dependencies. From this, we
recommend to set up a Conda environment and provide the requirements file as input. If you choose this option, please consult the
[Conda documentation]{https://docs.conda.io/en/latest/} for further details.

In addition to the code in this repository, a MISP server has to be configured and a new object template adapted to the ToN-IoT dataset form (column names, etc.) has to
be created. Also, the 'keys.py' module has to be completed, at least, with the MISP server URL and an user authentication key. An example of this part will be uploaded
soon.

## Launch
First, run the 'aggregator.py' module. This module has no command line parameters, so simply run:

```
python aggregator.py
```

Next, run the 'misp_retriever.py' module, providing the three main parameters 'retr-interval' (time interval for querying MISP for new data), 'inst_threshold' (# of
instances to register against the aggregator and consume the data) and 'aggregator_ip' (IP where the FL aggregator server is located) through command line. 

```
python misp_retriever.py --retr-interval=<retrieve interval in seconds> --inst-threshold=<number of instances> --aggregator-ip=<xx:xx:xx:xx>
```

If the instance threshold is reached, a FL client will be created and registered against the aggregator. However, the process will not start until at least a second
client joins the process. In order to do this, you need to set up a second client that can be:

  - A normal FL client that uses data from a static dataset file. For instance, assuming we have the ToN-IoT partitions in CSV files, a Flower client can be coded to
  load the data, preprocess it and register against the aggregator. To do this, please consult the 'FLClient.py' module code and Flower official documentation.
  - Another MISP-FL client (parallel to the previous one) that retrieves the data from its local MISP server. This can represent another organization.