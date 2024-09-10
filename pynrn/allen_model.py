import os, urllib.request, zipfile
import allensdk.model.biophysical as allensdk_model_biophysical
from allensdk.model.biophysical.runner import run, load_description
from allensdk.model.biophysical.utils import create_utils
from neuron import h
from .compile import compile_and_load_mechanisms
from .section import Section
from .context import Context

default_model_cache_path = os.path.join(os.path.dirname(__file__), 'allen_models')

def load_allen_cell(model_id, model_cache_path=None):
    """Downloads and loads an Allen Cell Types model into NEURON

    Requires the AllenSDK package to be installed. The model will be downloaded
    and compiled if it has not been downloaded before.
    """
    if model_cache_path is None:
        model_cache_path = default_model_cache_path

    # Make sure cell.hoc is present (some versions of the AllenSDK don't include it)    
    lib_path = os.path.dirname(allensdk_model_biophysical.__file__)
    hoc_file = os.path.join(lib_path, 'cell.hoc')
    if not os.path.exists(hoc_file):
        url = "https://raw.githubusercontent.com/AllenInstitute/AllenSDK/master/allensdk/model/biophysical/cell.hoc"
        urllib.request.urlretrieve(url, hoc_file)

    # Download the model
    model_path = os.path.join(model_cache_path, str(model_id))
    if not os.path.exists(model_path):
        try:
            if not os.path.exists(model_cache_path):
                os.mkdir(model_cache_path)
            os.mkdir(model_path)
            url = 'http://celltypes.brain-map.org/neuronal_model/download/%d' % model_id
            print("Downloading model %d from %s" % (model_id, url))
            zip_path = os.path.join(model_path, 'model.zip')
            urllib.request.urlretrieve(url, zip_path)
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(model_path)
            os.remove(zip_path)
        except Exception as e:
            # remove the directory and all files inside
            import shutil
            shutil.rmtree(model_path)
            raise e
        
    # Compile the mechanisms
    compile_and_load_mechanisms(os.path.join(model_path, 'modfiles'))

    existing_sections = list(h.allsec())

    # create a pynrn context if one does not exist yet (since we are about to create many sections)
    Context.active_context(create=True)

    # Load the model into NEURON
    os.chdir(model_path)        
    manifest_file = os.path.join(model_path, 'manifest.json')
    desc = load_description({'manifest_file': manifest_file})
    utils = create_utils(desc)
    morphology_path = desc.manifest.get_path('MORPHOLOGY').encode('ascii', 'ignore')
    morphology_path = morphology_path.decode("utf-8")
    utils.generate_morphology(morphology_path)
    utils.load_cell_parameters()

    updated_sections = list(h.allsec())
    newsec = {}
    for sec in updated_sections:
        if sec not in existing_sections:
            newsec[sec.name()] = Section(_nrnobj=sec)

    return newsec
