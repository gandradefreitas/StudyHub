# Operação do StudyHub

## Publicação

1. Execute os testes matemáticos e web separadamente. Os web exigem um PostgreSQL dedicado chamado `studyhub_test`.
2. Instale as dependências de `requirements.txt` da mesma revisão que será publicada. As versões diretas estão fixadas. Atualize-as em uma revisão própria e rode a suíte novamente.
3. Antes de migrar o banco publicado, obtenha um backup PostgreSQL ou um ponto de restauração do provedor. Valide em um banco isolado usando a mesma revisão do aplicativo.
4. Com `DATABASE_URL` apontando para o destino pretendido, execute `python -m database.criar_banco` uma vez. O processo registra as versões e serializa execuções concorrentes. O servidor web e o worker não aplicam migrações na inicialização.
5. Inicie `gunicorn app:app` e o processo indicado no [guia da fila de correções](fila-correcoes.md). Confira o endpoint `/health`, o login e as páginas autenticadas, e verifique o estado da fila.
6. Configure `STUDYHUB_PROXY_HTTPS=1` somente quando o servidor não puder ser acessado diretamente e houver exatamente um proxy confiável que substitua o cabeçalho de protocolo dos clientes. Confirme HTTPS, HSTS e a política de segurança de conteúdo no endereço publicado.

## Recuperação

O backup JSON em Configurações é uma exportação pessoal. Para restaurar o serviço, use um backup do PostgreSQL ou a restauração do provedor. Restaure primeiro em outro banco, confira a versão das migrações e faça uma rodada de validação antes de apontar o serviço para o banco recuperado. Mantenha as credenciais fora de arquivos versionados e logs.

## Diagnóstico

- **Site no ar e correções pendentes:** use `python worker_correcao_discursiva.py --status`. Cruze a idade da fila com os logs do worker. Confirme o banco configurado e a presença da chave Gemini no serviço de correção.
- **Falha após publicar:** compare as versões em `studyhub_migracoes` com os arquivos da revisão instalada. Use os logs da etapa de migração para identificar a primeira alteração que falhou.
- **Divergência de tempo ou notas:** compare o mesmo usuário e período nas Estatísticas, no Histórico e nas exportações. Diferencie as notas provisórias das notas finais.

## Testes no navegador

Com o `DATABASE_URL` configurado explicitamente para o PostgreSQL **local**
`studyhub_test`, execute o teste com Node.js 22 ou superior, o Python do ambiente
virtual e uma instalação do Chrome. A partir da raiz do projeto:

```text
node tests/browser/verificar_navegador.mjs <python> <chrome> .
```

O teste inicia um servidor temporário, cria e remove uma conta descartável,
bloqueia recursos externos e confere temas, navegação por teclado, criação e
edição de tarefas, os dados dos gráficos e a tabela móvel do Histórico.
