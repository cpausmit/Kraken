#===================================================================================================
#  C L A S S E S
#===================================================================================================
class Datasets:
    "Collection of datasets."
    def __init__(self):
        self.datasets = {}

    def add_dataset(self,dataset_name):
        if dataset_name not in self.datasets:
            self.datasets[dataset_name] = Dataset(dataset_name)
        return self.datasets[dataset_name]

    def show(self):
        for dataset_name in self.datasets:
            self.datasets[dataset_name].show()

class Dataset:
    "Minimal dataset description."
    def __init__(self,name):
        self.name = name
        self.blocks = {}

    def add_block(self,block_name):
        if block_name not in self.blocks:
            self.blocks[block_name] = Block(block_name)
        return self.blocks[block_name]

    def add_block_file(self,block_name,file_name,file_size):
        block = self.add_block(block_name)
        block.add_file(file_name,file_size)

    def show(self):
        print(" # Dataset: %s"%(self.name))
        for block_name in self.blocks:
            self.blocks[block_name].show()

    def json(self,time,site="T2_US_MIT"):

        (config,version,parent_dataset) = self.name.split('/')

        print(" Injecting into: %s"%(site))

        # fundamental json with blocks and files to be added
        json = { 'dataset':
                     [ { 'name': "%s"%(self.name),
                         'status': 'production',
                         'data_type': 'panda',
                         'software_version': (config, version),
                         'blocks': [ ]
                         } ],
                 'datasetreplica':
                     [ { 'site': site,
                         'growing': True,
                         'group': 'analysis',
                         'dataset': "%s"%(self.name),
                         'blockreplicas': [ ]
                         } ]
                 }

        # add the block components to the dataset and the datasetreplica
        for block_name in self.blocks:
            jb_dataset = { 'name': block_name,
                           'files': self.blocks[block_name].json(site)
                           }
            jb_replica = { 'last_update': time,
                           'group': 'analysis',
                           'block': block_name }

            # append the two pieces to the json
            json['dataset'][0]['blocks'].append(jb_dataset)
            json['datasetreplica'][0]['blockreplicas'].append(jb_replica)

        return json

    def json_replica(self,time,site="T2_US_MIT"):

        (config,version,parent_dataset) = self.name.split('/')

        print(" Injecting into: %s"%(site))

        # fundamental json with blocks and files to be added
        json = { 'datasetreplica':
                     [ { 'site': site,
                         'growing': True,
                         'group': 'analysis',
                         'dataset': "%s"%(self.name),
                         'blockreplicas': [ ]
                         } ]
                 }

        # add the block components to the dataset and the datasetreplica
        for block_name in self.blocks:
            jb_replica = { 'last_update': time,
                           'group': 'analysis',
                           'block': block_name }

            # append the piece to the json
            json['datasetreplica'][0]['blockreplicas'].append(jb_replica)

        return json

class Block:
    "Minimal block description."
    def __init__(self,name):
        self.name = name
        self.sizes = {}

    def add_file(self,name,size):
        self.sizes[name] = size

    def show(self):
        print(" ## Block: %s"%(self.name))
        for file_name in self.sizes:
            print(" %s -- %d"%(file_name,self.sizes[file_name]))

    def json(self,site="T2_US_MIT"):
        json = []
        for file_name in self.sizes:
            json.append({'name': file_name,'size': self.sizes[file_name],'site': site})

        return json
