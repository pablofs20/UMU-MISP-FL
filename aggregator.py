import flwr as fl
import configparser

CONF_FILE = 'resources/fl.ini'

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read(CONF_FILE)
    
    rounds = int(config['FL Aggregator']['Rounds'])
    ip = config['FL Aggregator']['IP']
    port = config['FL Aggregator']['Port']

    fl.server.start_server(server_address = '{ip}:{port}' \
            .format(ip = ip, port = port), config={"num_rounds": rounds})
