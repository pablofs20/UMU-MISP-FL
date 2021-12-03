import flwr as fl
import configparser

CONF_FILE = 'resources/fl.ini'

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read(CONF_FILE)
    
    rounds = int(config['FL Aggregator']['Rounds'])

    fl.server.start_server(config={"num_rounds": rounds})
