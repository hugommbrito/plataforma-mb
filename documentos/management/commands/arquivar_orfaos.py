"""
Varre o bucket R2 e move para arquivo-morto/ qualquer arquivo que não
corresponda a um registro ativo em Documento.arquivo.

Uso:
    python manage.py arquivar_orfaos           # move de verdade
    python manage.py arquivar_orfaos --dry-run # só lista, não move
"""

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from documentos.models import Documento

ARQUIVO_MORTO = 'arquivo-morto'


def _get_client():
    """Cria client boto3 direto com configuração explícita para Cloudflare R2."""
    required = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_STORAGE_BUCKET_NAME', 'AWS_S3_ENDPOINT_URL']
    missing = [k for k in required if not getattr(settings, k, None)]
    if missing:
        raise CommandError(f'Variáveis não configuradas: {", ".join(missing)}')

    return boto3.client(
        's3',
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        config=Config(
            s3={'addressing_style': 'path'},
            signature_version='s3v4',
            connect_timeout=15,
            read_timeout=30,
        ),
    )


class Command(BaseCommand):
    help = 'Move arquivos órfãos do R2 para arquivo-morto/'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Lista os órfãos sem mover nada.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write('Conectando ao R2...')
        try:
            client = _get_client()
        except CommandError:
            raise
        except Exception as e:
            raise CommandError(f'\n\nErro ao criar client S3: {e}')

        bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        self.stdout.write(f'Bucket: {bucket_name}\n\n')

        self.stdout.write('Consultando banco de dados...')
        db_paths = set(
            Documento.objects.exclude(arquivo='').values_list('arquivo', flat=True)
        )
        self.stdout.write(f'    - {len(db_paths)} arquivo(s) registrado(s) no banco.\n\n')

        self.stdout.write('Listando objetos no bucket...')
        orfaos = []
        try:
            paginator = client.get_paginator('list_objects_v2')
            total_bucket = 0
            for page in paginator.paginate(Bucket=bucket_name):
                for obj in page.get('Contents', []):
                    key = obj['Key']
                    total_bucket += 1
                    if key.startswith(f'{ARQUIVO_MORTO}/'):
                        continue
                    if key not in db_paths:
                        orfaos.append(key)
        except (BotoCoreError, ClientError) as e:
            raise CommandError(f'\n\nErro ao listar bucket: {e}')

        self.stdout.write(f'    - {total_bucket} objeto(s) encontrado(s) no bucket.\n\n')

        if not orfaos:
            self.stdout.write(self.style.SUCCESS('\nNenhum arquivo órfão encontrado.\n\n'))
            return

        self.stdout.write(f'{len(orfaos)} arquivo(s) órfão(s) encontrado(s):')

        movidos = 0
        for key in orfaos:
            destino = f'{ARQUIVO_MORTO}/{key}'
            self.stdout.write(f'  {key}  →  {destino}')
            if not dry_run:
                try:
                    client.copy_object(
                        Bucket=bucket_name,
                        CopySource={'Bucket': bucket_name, 'Key': key},
                        Key=destino,
                    )
                    client.delete_object(Bucket=bucket_name, Key=key)
                    movidos += 1
                except (BotoCoreError, ClientError) as e:
                    self.stderr.write(f'  ERRO ao mover {key}: {e}')

        if dry_run:
            self.stdout.write(self.style.WARNING('\n\nDry-run: nenhum arquivo foi movido.\n\n'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\n\n{movidos} arquivo(s) movido(s) para {ARQUIVO_MORTO}/.\n\n'))
