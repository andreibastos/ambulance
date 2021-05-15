# Downloads de Imagens via google imagens
## Requisitos
- Chrome
- Python
- Virtualenv
  
# Passos 
1. Baixe o chromedriver 
- https://chromedriver.chromium.org/downloads
e salve na pasta scrapper-images

2. Configurar o ambiente
```bash
virtualenv ENV
source ENV/bin/activate
pip3 install -r requirements
```

# Execução
```bash
# buscar uma palavra
python3 scrapper.py -q maçã

# buscar duas palavra
python3 scrapper.py -q maçã banana

# buscar duas palavra com limite de 100
python3 scrapper.py -q maçã banana -c 100

# buscar duas palavra com limite de 100 imagens na pasta imgs
python3 scrapper.py -q maçã banana -c 100 -i imgs

# buscar duas palavra com limite de 100 imagens na pasta imgs e links na pasta link
python3 scrapper.py -q maçã banana -c 100 -i imgs -l link
```

