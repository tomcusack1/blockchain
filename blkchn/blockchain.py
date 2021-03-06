from hashlib import sha256
import json
import logging
import requests
from time import time


logging.basicConfig(level=logging.DEBUG)


class Blockchain:
    """A Blockchain data structure.

    Attributes:
      current_transactions (list): A list of all the pending transactions
      chain (list): A record of all the blocks within the Blockchain
      nodes (set): A unique collection of all connected nodes (e.g. {192.168.0.5:5000})

    """
    def __init__(self):
        self.current_transactions = list()
        self.chain = list()
        self.nodes = set()
        self.new_block(previous_hash='1', proof=100)

    def register_node(self, address: str) -> None:
        """Adds a new node to the list of nodes

        Args:
            address (str): Address of a node. E.g. '192.168.0.5:5000'

        Returns:
            None: If successful, else raises a ValueError

        """
        logging.info(f'Adding `{address}` to registered nodes list.')
        self.nodes.add(address)

    def valid_chain(self, chain: dict) -> bool:
        """Determines if a given blockchain is valid

        Args:
          chain (dict): A list of dictionaries (blocks) making up a blockchain

        Returns:
            bool: True if valid, False if not

        """
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            last_block_hash = self.hash(last_block)

            if block['previous_hash'] != last_block_hash:
                # Check that the hash of the block is correct
                logging.critical('Previous hash does not equal the last blocks hash!')
                return False

            if not self.valid_proof(last_block['proof'], block['proof'], last_block_hash):
                # Check that the Proof of Work is correct
                logging.critical('The last blocks hash is malformed. The blockchain is corrupt.')
                return False

            last_block = block
            current_index += 1

        logging.info('Success. Chain is valid.')

        return True

    def resolve_conflicts(self) -> bool:
        """The consensus algorithm

        Resolves conflicts by replacing the chain with the longest one in the network.

        Returns:
            bool: True if our chain was replaced, False if not

        """
        neighbours = self.nodes
        new_chain = None
        max_length = len(self.chain)  # We're only looking for chains longer than ours

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            logging.info(f'Fetching chain from: {node}')
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we have discovered a new, __valid chain__, longer than ours
        if new_chain:
            self.chain = new_chain
            logging.warning('Replacing chain with a newer, longer, valid chain.')
            return True

        return False

    def new_block(self, proof: int, previous_hash: str) -> dict:
        """Creates a new Block on the Blockchain

        Args:
          proof: The proof given by the Proof of Work algorithm
          previous_hash: Hash of previous Block

        Returns:
          dict: New Block

        """
        self.current_transactions = list()  # Reset the current list of transactions
        self.chain.append({
            'index': len(self.chain) + 1,
            'created_at': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        })

        logging.info('Success. New block created.')

        return self.chain[-1]

    def new_transaction(self, transaction: dict) -> int:
        """Creates a new transaction to go into the next mined block

        The dictionary passed in can contain any data

        Args:
          transaction (dict): A dictionary representation of a transaction

        e.g.

          {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'quantity': quantity,
            'created_at': time()
          }

        Returns:
          int: The index of the block that will hold this transaction

        """
        self.current_transactions.append(transaction)

        logging.info('Success. New transaction created.')

        return self.last_block['index'] + 1

    @property
    def last_block(self) -> dict:
        """Returns the last block on the blockchain."""

        return self.chain[-1]

    @staticmethod
    def hash(block: dict) -> str:
        """Creates a SHA-256 hash of a Block

        We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes

        Args:
          block (dict): A single block on the blockchain

        Returns:
          str: A hash of the block

        """
        block_string = json.dumps(block, sort_keys=True).encode()

        return sha256(block_string).hexdigest()

    def proof_of_work(self, last_block) -> int:
        """Proof of Work Algorithm

        Repeatedly hashes incrementing the nonce value until the hash has N zeros at the beginning.

        Args:
          last_block (dict): The last block to have been placed on the blockchain

        Returns:
          int: The proof of work

        """
        proof = 0

        while not self.valid_proof(last_proof=last_block['proof'], proof=proof, last_hash=self.hash(last_block)):
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof: int, proof: int, last_hash: str) -> bool:
        """Validates the Proof

        Args:
          last_proof (int): Previous Proof
          proof (int): Current Proof
          last_hash (int): The hash of the Previous Block

        Returns:
          bool: True if correct, False if not.

        """
        guess = f'{last_proof}{proof}{last_hash}'.encode()

        return sha256(guess).hexdigest()[:4] == '0000'
