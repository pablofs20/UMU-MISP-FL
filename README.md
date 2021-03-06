# FL-trained ML models using real-time MISP data

## Overview
This demo aims to leverage the data coming from a MISP server to train a ML model using Federated Learning (FL). The main objective is to provide and test an alternative
method for an organization to use the IoCs shared through MISP and give a feedback. Once enough data has been received by the client, a FL process is triggered along with
an aggregator and some other clients, and a final model, trained collaboratively by all of the clients with their local data, is obtained. This resulting model is fed
back to the local MISP server and, therefore, it can be used by other involved organizations to deploy it in, e.g., an anomaly-based IDS.

For this experiment, we use several partitions of the [ToN-IoT dataset](https://research.unsw.edu.au/projects/toniot-datasets), one per configured client. Each partition, representing the data which would belong to a specific
organization, is used by a producer (see `producer.py`) to feed the MISP server on one side, creating and uploading MISP events which contain one or multiple dataset instances, encoded as MISP objects. On the other side, a consumer module will periodically ask the MISP server for new 
events and, once it has enough data, will register against the FL aggregator that is meant to be running from the beginning of the whole process (see `aggregator.py`). When the number of clients
connected to the aggregator is equal or higher than 2, the FL process begins and a ML model is trained collaboratively by the registered clients. Finally, this
model is pushed back to the MISP server as an event with an attachment containing the ML model, from where it is shared to other domains. This workflow can be consulted in detail in the following sequence diagrams:

<p align="center">
  <img src="https://github.com/pablofs20/misp-fl/blob/master/images/sequence_producer.png?raw=true" alt="Sublime's custom image"/>
  <img src="https://github.com/pablofs20/misp-fl/blob/master/images/sequence_consumer.png?raw=true" alt="Sublime's custom image"/>
</p>

In addition, we shall remark that, currently in this first version, the timestamp of the last processed event is saved to a local file `last_timestamp` inside the `resources` folder. It should be noted that the initial timestamp is set to 0 in order to retrieve all the available events (first execution).

For the FL part, we leverage the Flower framework. Please consult the [Flower official documentation](https://flower.dev/docs/) for further details. We also provide some examples of lightweight ToN-IoT partitions under `data` folder, each one containing 1000 samples and 5 different labels/attacks (benign, xss, injection, password and scanning) for testing purposes.

## Configuration
This software is coded and tested in Python 3.6.9. Since multiple libraries have been employed, we provide a Python requirements file under `resources` folder containing all the dependencies. From this, we
recommend to set up a Conda/Miniconda environment and provide the requirements file as input. If you choose this option, please consult the
[Conda documentation](https://docs.conda.io/en/latest/) for further details.

In addition to the code in this repository, a MISP server has to be configured and a new object template adapted to the ToN-IoT dataset form has to
be created. We provide the object definition file used for testing inside `misp` folder. Also, the `keys.py` module has to be completed, at least, with the MISP server URL and a user authentication key.

By last, some of the main FL parameters, for both the aggregator and the clients, can be customized in the `resources/fl.ini` configuration file. Inside it, a brief description of each one is given.

## Execution
First, launch the `aggregator.py` module. This module does not expect any command line parameters, so simply run:

```
python aggregator.py
```

Next, run the `consumer.py` module, providing the two main parameters `--retrieve_interval` or `-r` (time interval for querying MISP for new data) and `--inst_threshold` or `-i` (# of
instances needed to register against the aggregator and consume the data) through command line: 

```
python consumer.py --retr_interval=<retrieve interval in seconds> --inst_threshold=<number of instances>
```

By last, run the `producer.py` module, providing the two main parameters `--nobjects` or `-n` (number of desired objects per event) and `--data_source` or `-d` (data source file). To launch it with the provided data files, set this last parameter to one of the three `data/ton_iot_1.csv`, `data/ton_iot_2.csv` or `data/ton_iot_3.csv`:

```
python producer.py --nobjects=<objects per event> --data_source=<data source filename>
```

If the instance threshold is reached, a Flower FL client (see `FLClient.py`) will be created by the consumer, and will register automatically against the aggregator. However, the process will not start until at least a second
client joins the process. In order to do this, you need to set up a second client that can be:

  - A dummy FL client that uses data from a static dataset file. As a suggestion, create a Flower client that loads the data from any of the partitions we provide in this repository. To do this from scratch, please refer [Flower official documentation](https://flower.dev/docs/). However, we have also provided an example named `auxiliary_client.py` under the root folder for quick testing.
  - Another consumer module similar to the described one, but configured to work with a different MISP server which would represent another organization/domain. To do so, you can reuse the consumer module but tweaking the parameters in the `keys.py` file.
