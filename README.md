# Projeto de Grupo — Computação Visual

Projeto da disciplina de Computação Visual da Universidade do Algarve. A aplicação usa
Python e OpenCV para detetar movimento da webcam e apresentar animações renderizadas no
Blender sobre a imagem da câmara.

## Grupo

- Laura Kayamori
- Maria Eduarda Pereira
- Nicolas Takuma
- Fernando Davila

## Como funciona

1. A câmara fornece imagens em tempo real, refletidas horizontalmente.
2. O MOG2 separa o movimento do fundo. A máscara é filtrada e os contornos com área
   suficiente originam caixas delimitadoras.
3. O centro de cada caixa determina a zona onde houve movimento. Podem existir eventos
   em várias zonas ao mesmo tempo.
4. A aplicação escolhe o fotograma das animações dessa zona e compõe os PNG com o canal
   alfa sobre uma cópia da imagem da câmara.
5. Um vídeo da sessão, capturas manuais e um registo JSON guardam as evidências.

## Zonas e reações

| Zona | Objetos | Reação na aplicação | Autoria dos modelos |
|---|---|---|---|
| Esquerda | Cadeira e vaso | Os dois objetos aparecem junto ao centro do movimento. | A completar pelo grupo |
| Centro | Mesa | O tamanho do objeto varia com o tamanho da maior caixa detetada. | A completar pelo grupo |
| Direita | Prato e copo | A velocidade da animação varia com a direção horizontal do movimento. | A completar pelo grupo |

Cada zona tem o seu próprio evento. Depois do último movimento, o evento permanece aberto
por 0,65 segundos. Na versão atual, as animações são desenhadas enquanto há deteção na zona.

## Estrutura

| Caminho | Responsabilidade |
|---|---|
| `src/main.py` | Lê a configuração e inicia a aplicação. |
| `src/app/application.py` | Coordena o ciclo principal e as reações das zonas. |
| `src/app/config.py` | Define caminhos, opções e parâmetros. |
| `src/app/camera.py` | Abre a câmara e lê imagens refletidas. |
| `src/app/vision.py` | Deteta movimento, agrupa caixas por zona e desenha-as. |
| `src/app/animations.py` | Carrega as sequências PNG e compõe as animações. |
| `src/app/events.py` | Gere os eventos por zona e escreve o JSON. |
| `src/app/recorder.py` | Gere a gravação da sessão e as capturas. |
| `src/app/logger.py` | Mostra mensagens na consola. |
| `assets/` | Sequências PNG das animações, uma pasta por objeto. |
| `blender/` | Ficheiros de trabalho do Blender. |
| `evidencias/` | Vídeos, capturas e registos gerados pela aplicação. |

## Preparação e execução

É necessária uma webcam, Python 3.12, OpenCV, NumPy e Rich. A partir da pasta raiz,
uma forma de preparar o ambiente com `uv` é:

```powershell
uv venv --python 3.12
uv pip install -r requirements.txt
```

No Windows, execute o programa usando o Python desse ambiente:

```powershell
.\.venv\Scripts\python.exe src/main.py
```

A aplicação usa OpenCV 5.x (`opencv-python>=5.0,<6`). Se não for possível instalar
essa versão, pode usar OpenCV 4.14 no ambiente local e executar com o Python da `.venv`;
`uv run` continuará a pedir OpenCV 5.x através do cabeçalho de `src/main.py`.

Opções disponíveis: `--camera` (predefinição `0`), `--min-area` (`700` píxeis quadrados),
`--fps` (`24` no vídeo gravado) e `--warmup` (`50` fotogramas de estabilização).
Por exemplo, para usar outra câmara:

```powershell
.\.venv\Scripts\python.exe src/main.py --camera 1
```

Na janela, prima **S** para guardar uma captura e **Q** para terminar.

## Evidências e registo

Cada execução grava um MP4 da sessão com as zonas, caixas e animações desenhadas, e um
JSON associado com os eventos terminados. Cada evento inclui a zona, início em ISO 8601,
duração, caminho do vídeo e amostras das caixas. A tecla S guarda um PNG da imagem
apresentada. Os ficheiros são identificados pela data e hora de criação.

Os MP4 em `evidencias/` estão ignorados pelo Git, mas a configuração atual **não ignora**
automaticamente os PNG e JSON dessa pasta. Verifique os ficheiros antes de os adicionar a
um commit, sobretudo porque podem conter imagens de pessoas.

## Utilização de IA no código

Claude, Codex e AstraAI foram utilizados para refatorizar o código, mantendo a lógica
previamente desenvolvida pelo grupo.
