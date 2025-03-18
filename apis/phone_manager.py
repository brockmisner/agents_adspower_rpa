import json
import os
import time
import logging
from datetime import datetime, timedelta
import requests

logger = logging.getLogger(__name__)


class PhoneManager:
    """
    Gerencia números de telefone, permitindo reutilização de números recentes.
    Otimiza uso de créditos do serviço SMS guardando números que ainda podem ser usados.
    """

    def __init__(self, storage_path="credentials/phone_numbers.json"):
        """
        Inicializa o gerenciador de números de telefone.

        Args:
            storage_path: Caminho para o arquivo JSON de armazenamento
        """
        self.storage_path = storage_path
        self.numbers = self._load_numbers()
        self.reuse_window = 30 * 60  # 30 minutos em segundos - janela de reutilização
        self.api_key = self.load_api_key()

    def _load_numbers(self):
        """Carrega os números do arquivo de armazenamento."""
        if not os.path.exists(self.storage_path):
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            return []

        try:
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save_numbers(self):
        """Salva os números no arquivo de armazenamento."""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, 'w') as f:
            json.dump(self.numbers, f, indent=4)

    def add_number(self, phone_number, country_code, activation_id, service="go"):
        """
        Adiciona ou atualiza um número no gerenciador.
        """
        if not all([phone_number, country_code, activation_id]):
            logger.error("❌ Dados de telefone incompletos, não será salvo")
            return False

        current_time = time.time()

        # Verificar se o número já existe
        for number in self.numbers:
            if number["phone_number"] == phone_number:
                # Atualizar dados existentes
                number["last_used"] = current_time
                number["times_used"] += 1
                if service not in number["services"]:
                    number["services"].append(service)
                self._save_numbers()
                logger.info(
                    f"✅ Número {phone_number} atualizado no gerenciador")
                return True

        # Adicionar novo número
        new_number = {
            "phone_number": phone_number,
            "country_code": country_code,
            "activation_id": activation_id,
            "first_used": current_time,
            "last_used": current_time,
            "services": [service],
            "times_used": 1
        }

        self.numbers.append(new_number)
        self._save_numbers()
        logger.info(f"✅ Número {phone_number} adicionado ao gerenciador")
        return True

    def get_reusable_number(self, service="go"):
        """
        Obtém um número reutilizável que ainda está dentro da janela de validade.

        Args:
            service: Código do serviço para o qual o número será usado

        Returns:
            dict: Informações do número reutilizável ou None se não houver
        """
        current_time = time.time()
        valid_numbers = []

        # Limpar números expirados
        self._cleanup_expired_numbers()

        # Buscar números válidos
        for number in self.numbers:
            time_since_last_use = current_time - number["last_used"]

            # Verificar se está dentro da janela de reutilização
            if time_since_last_use < self.reuse_window:
                # Verificar se o número não foi usado para este serviço
                if service not in number["services"]:
                    valid_numbers.append(number)

        # Ordenar por menos utilizado primeiro
        valid_numbers.sort(key=lambda x: x["times_used"])

        if valid_numbers:
            # Atualizar o número selecionado
            selected = valid_numbers[0]
            selected["last_used"] = current_time
            selected["times_used"] += 1
            selected["services"].append(service)
            self._save_numbers()

            time_left = self.reuse_window - \
                (current_time - selected["first_used"])
            minutes_left = int(time_left / 60)

            logger.info(
                f"♻️ Reutilizando número {selected['phone_number']} ({minutes_left} minutos restantes)")
            return selected

        return None

    def _cleanup_expired_numbers(self):
        """Remove números que já expiraram da janela de reutilização."""
        current_time = time.time()
        self.numbers = [
            number for number in self.numbers
            if (current_time - number["first_used"]) < self.reuse_window
        ]
        self._save_numbers()

    def mark_number_used(self, phone_number, service="go"):
        """
        Marca um número como usado para um determinado serviço.

        Args:
            phone_number: Número de telefone
            service: Código do serviço
        """
        for number in self.numbers:
            if number["phone_number"] == phone_number:
                number["last_used"] = time.time()
                number["times_used"] += 1
                if service not in number["services"]:
                    number["services"].append(service)
                self._save_numbers()
                return True
        return False

    def get_stats(self):
        """
        Retorna estatísticas sobre os números gerenciados.

        Returns:
            dict: Estatísticas de uso dos números
        """
        total_numbers = len(self.numbers)
        total_uses = sum(number.get("times_used", 0)
                         for number in self.numbers)
        active_numbers = sum(
            1 for number in self.numbers if number.get("is_active", False))

        # Contar serviços utilizados
        total_services = sum(len(number.get("services", []))
                             for number in self.numbers)

        return {
            "total_numbers": total_numbers,
            "total_uses": total_uses,
            "active_numbers": active_numbers,
            "total_services": total_services,
            "estimated_savings": self.calculate_estimated_savings()
        }

    def calculate_estimated_savings(self):
        """Calcula a economia estimada com base no uso dos números."""
        total_savings = 0
        for number in self.numbers:
            # Supondo que você tenha um campo 'savings_per_use' em cada número
            savings_per_use = number.get("savings_per_use", 0)
            times_used = number.get("times_used", 0)
            total_savings += savings_per_use * times_used
        return total_savings

    def load_api_key(self):
        """Carrega a chave da API do arquivo de credenciais."""
        try:
            with open("credentials/credentials.json", "r") as file:
                credentials = json.load(file)
                return credentials.get("SMS_ACTIVATE_API_KEY", None)
        except Exception as e:
            logging.error(f"Erro ao carregar a chave da API: {str(e)}")
            return None

    def cancel_number(self, number_id):
        """
        Cancela um número na API do SMS Activate.

        Args:
            number_id (str): O ID do número a ser cancelado.

        Returns:
            bool: True se o cancelamento foi bem-sucedido, False caso contrário.
        """
        url = "https://sms-activate.guru/stubs/handler_api.php"
        params = {
            "api_key": self.api_key,  # Usar a chave de API carregada
            "action": "cancel",
            "id": number_id
        }

        try:
            response = requests.post(url, params=params)
            response_data = response.text

            if "STATUS_OK" in response_data:
                logging.info(f"Número {number_id} cancelado com sucesso.")
                return True
            else:
                logging.error(
                    f"Erro ao cancelar número {number_id}: {response_data}")
                return False
        except Exception as e:
            logging.error(
                f"Erro ao fazer requisição para cancelar número: {str(e)}")
            return False

    def remove_number(self, phone_number):
        """
        Remove um número do gerenciador.

        Args:
            phone_number (str): O número de telefone a ser removido.

        Returns:
            bool: True se a remoção foi bem-sucedida, False caso contrário.
        """
        for i, number in enumerate(self.numbers):
            if number["phone_number"] == phone_number:
                del self.numbers[i]  # Remove o número da lista
                self._save_numbers()  # Salva as alterações no arquivo
                logging.info(f"Número {phone_number} removido com sucesso.")
                return True
        logging.warning(f"Número {phone_number} não encontrado.")
        return False
