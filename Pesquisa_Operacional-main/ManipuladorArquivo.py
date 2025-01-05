import re


class ManipuladorArquivo:
    def __init__(self, nome_arquivo_entrada):
        self.nome_arquivo_entrada = nome_arquivo_entrada
        self.conteudo = None
        self.ler_arquivo()

    def ler_arquivo(self):
        with open(f"{self.nome_arquivo_entrada}.txt", "r") as arquivo_entrada:
            self.conteudo = arquivo_entrada.read()

    def obter_tipo(self):
        type_match = re.search(r"type=(\w+)", self.conteudo)
        return type_match.group(1)

    def obter_n_clients(self):
        n_match = re.search(r"n=(\d+)", self.conteudo)
        return int(n_match.group(1))

    def obter_m_facilities(self):
        m_match = re.search(r"m=(\d+)", self.conteudo)
        return int(m_match.group(1))

    def obter_p_desired_facilities(self):
        p_match = re.search(r"p=(\d+)", self.conteudo)
        return int(p_match.group(1))

    def obter_clientes(self):
        clients_match = re.search(r"clients = \{(.*?)\}", self.conteudo, re.DOTALL)
        clients_value = [s.strip() for s in clients_match.group(1).split(",")]
        return clients_value

    def obter_facilidades(self):
        facilities_match = re.search(
            r"facilities = \{(.*?)\}", self.conteudo, re.DOTALL
        )
        facilities_value = [s.strip() for s in facilities_match.group(1).split(",")]
        return facilities_value

    def obter_distancias_facilidades(self):
        conteudo_sem_quebras = self.conteudo.replace("\n", "")
        variaveis = re.split(r"table =", conteudo_sem_quebras)[-1]
        variaveis = variaveis.replace("{", "[").replace("}", "]")
        variaveis = eval(variaveis)
        return variaveis
