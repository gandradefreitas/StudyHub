# Fila de correções

O servidor web salva provas e redações e retorna ao aluno a página de resultado. O worker usa o mesmo PostgreSQL para corrigir em segundo plano. Um processo interrompido deixa uma reserva temporária no banco e outro pode assumir a correção após a expiração. Uma reserva que expirou não pode gravar o resultado de uma rodada nova.

## Execução local

Na pasta do StudyHub, configure as variáveis de ambiente que você usa no site. Execute `python -m database.criar_banco` para aplicar as migrações. Use `python executar_local.py` para iniciar o site e o worker em processos separados. Pressionar Ctrl+C encerra ambos. Se preferir executá-los em terminais distintos, use `python app.py` e `python worker_correcao_discursiva.py`. Não é necessário iniciar a fila ao entrar no site nem depender do Agendador de Tarefas do Windows.

O worker precisa de `DATABASE_URL` e `GEMINI_API_KEY`. Ao usar um banco cujo nome difira de `studyhub` ou `studyhub_test`, configure também `STUDYHUB_BANCO_WORKER` com o nome real do banco de destino.

## Publicação

Configure o worker como processo dedicado com reinício após falha. No Render, use um Background Worker apontado para o mesmo repositório, revisão e diretório do serviço web. Use `python worker_correcao_discursiva.py` como comando de inicialização e as mesmas credenciais do PostgreSQL e Gemini, configuradas como segredos do serviço. Preencha `STUDYHUB_BANCO_WORKER` com o nome do banco configurado no Neon. Aplique as migrações antes de iniciar os processos web e worker.

Em uma implantação que usava simultaneamente o worker antigo, interrompa-o antes de iniciar o novo. Cada tentativa deve ser controlada pelo mecanismo de reserva do worker atual.

## Monitoramento e recuperação

Execute `python worker_correcao_discursiva.py --status` para ver as quantidades pendentes, em processamento, reagendadas e com falha, além da idade do registro pendente mais antigo. O worker também registra esses totais nos logs a cada cinco minutos, sem incluir o conteúdo enviado pelo aluno. Verifique se o serviço está em execução e se o banco esperado e a chave Gemini estão configurados caso a idade da fila continue subindo.

O cliente HTTP do Gemini usa limite de 60 segundos por chamada, sem repetição no cliente. As reservas duram cinco minutos para redações e dez para discursivas. Cada trabalho tem até quatro tentativas automáticas. Falhas temporárias são reagendadas após 30 segundos, 2 minutos e 5 minutos. Se o processo interromper a última tentativa, o worker marca a falha ao expirar a reserva. O aluno pode reenfileirar uma avaliação que esgotou as tentativas. O texto continua salvo e uma nota já concluída permanece no Histórico e nas médias.

Para verificar uma correção de cada modalidade em ambiente de testes ou manutenção, use `python worker_correcao_discursiva.py --uma-vez`. Esse comando processa itens reais do banco apontado por `DATABASE_URL`.


### Serviço web sem worker separado

Configure `STUDYHUB_BANCO_WORKER` com o nome do banco Neon (por exemplo `neondb`) e
`GEMINI_API_KEY` no serviço web. Use este **Start Command** após publicar o código:

```sh
python -m database.criar_banco && exec python executar_local.py --render
```

O Gunicorn usa a porta do Render e o worker consome a mesma fila. Enquanto o serviço
web estiver suspenso, os envios podem permanecer pendentes. Use o worker separado
quando precisar de processamento independente do ciclo de vida do site.
