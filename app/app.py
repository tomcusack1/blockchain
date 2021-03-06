from os import environ
import logging
from uuid import uuid4

from flask import Flask, jsonify, request

from blkchn import Blockchain


app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)
node_identifier = str(uuid4()).replace('-', '')
blockchain = Blockchain()


@app.route('/mine', methods=['GET'])
def mine():
    # We run the proof of work algorithm to get the next proof...
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block)

    # We must receive a reward for finding the proof.
    # The sender is `0` to signify that this node has mined a new coin.
    blockchain.new_transaction({'sender': '0', 'recipient': node_identifier, 'amount': 1})

    # Forge the new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    return jsonify({
        'message': 'New Block Forged',
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    """Stores a new transaction within the current block.

    Note:
      As a developer, it is your responsibility to define a model and strictly adhere to it. Theoretically,
      any dictionary can be stored into a block, but in practice, strict guard clauses should be implemented.

    Returns:
      201: On Creation
      400: Invalid JSON sent to server

    """
    values = request.get_json()

    if not all(k in values for k in ['sender', 'recipient', 'amount']):
        return 'Missing values', 400

    blockchain.new_transaction({
        'sender': values['sender'],
        'recipient': values['recipient'],
        'amount': values['amount']
    })

    return '', 201


@app.route('/chain', methods=['GET'])
def full_chain():
    """Returns the whole blockchain."""

    return jsonify({'chain': blockchain.chain, 'length': len(blockchain.chain)}), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    """Registers a new node to the network."""
    values = request.get_json()
    nodes = values.get('nodes')

    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    return jsonify({
        'message': 'New node added.',
        'connected_nodes': list(blockchain.nodes),
    }), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    """Resolves a chain by requesting consensus on the network."""
    if blockchain.resolve_conflicts():
        return jsonify({'message': 'Our chain was replaced', 'new_chain': blockchain.chain}), 200
    else:
        return jsonify({'message': 'Our chain is authoritative', 'new_chain': blockchain.chain}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=environ.get('DEBUG_MODE', True))
