from typing import Dict


class Config:
    def __init__(self, args: Dict):
        self.data_dir = args.get("data_dir")
        self.loss = args.get("loss")
        self.nb_epochs = args.get("nb_epochs")
        self.batch_size = args.get("batch_size")
        self.embedding_dimension = args.get("embedding_dimension")
