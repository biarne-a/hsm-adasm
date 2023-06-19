from typing import Dict
import tensorflow as tf
from tensorflow import keras

from train.losses import VanillaSoftmaxLoss, SampledSoftmaxLoss


class Gru4RecModel(keras.models.Model):
    def __init__(self, movie_id_counts: Dict[int, int], loss_name: str, embedding_dimension: int):
        super().__init__()
        movie_id_counts = list(movie_id_counts.items())
        movie_id_vocab = [movie_id for movie_id, count in movie_id_counts]
        movie_id_counts = [count for movie_id, count in movie_id_counts]
        self._movie_id_lookup = tf.keras.layers.StringLookup(vocabulary=movie_id_vocab)
        self._movie_id_embedding = tf.keras.layers.Embedding(len(movie_id_counts) + 1, embedding_dimension)
        self._gru_layer = tf.keras.layers.GRU(embedding_dimension)
        self._loss = self._get_loss(loss_name, movie_id_counts)

    def _get_loss(self, loss_name, movie_id_counts):
        if loss_name == "vanilla-sm":
            return VanillaSoftmaxLoss(self._movie_id_embedding)
        if loss_name == "sampled-sm":
            return SampledSoftmaxLoss(movie_id_counts, self._movie_id_embedding)
        raise Exception(f"Unknown loss {loss_name}")

    def call(self, inputs, training=False):
        ctx_movie_idx = self._movie_id_lookup(inputs["context_movie_id"])
        ctx_movie_emb = self._movie_id_embedding(ctx_movie_idx)
        return self._gru_layer(ctx_movie_emb)

    def train_step(self, inputs):
        # Forward pass
        with tf.GradientTape() as tape:
            logits = self(inputs, training=True)
            label = self._movie_id_lookup(inputs["label_movie_id"])
            loss_val = self._loss(label, logits)

        # Backward pass
        self.optimizer.minimize(loss_val, self.trainable_variables, tape=tape)

        return {"loss": loss_val}

    def test_step(self, inputs):
        # Forward pass
        logits = self(inputs, training=False)
        label_movie_idx = self._movie_id_lookup(inputs["label_movie_id"])
        loss_val = self._loss(label_movie_idx, logits)

        # Compute metrics
        # We add one to the output indices because everything is shifted because of the OOV token
        top_indices = tf.math.top_k(logits, k=1000).indices + 1
        metric_results = self.compute_metrics(x=None, y=label_movie_idx, y_pred=top_indices, sample_weight=None)

        return {"loss": loss_val, **metric_results}
