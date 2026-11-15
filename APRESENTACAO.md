# Roteiro de fala — apresentação final (10 a 15 minutos)

## Luis Felipe Placco — Introdução e arquitetura
"Nosso projeto é um processador de transações em lote, executado no terminal com Python. Ele lê dez casos de um JSON, valida cada transação, calcula descontos, salva os resultados no SQLite e registra logs. Organizamos o código em três camadas: regras de negócio, persistência e aplicação CLI. O objetivo principal é mostrar as práticas de DevOps."

## Isabella Mozzer Hakime — Qualidade e testes
"A validação exige valor positivo, idade de zero a 120 e CPF com onze dígitos. Menores não compram eletrônicos. Para descontos, idosos têm quinze por cento e livros dez por cento, acumuláveis até vinte e cinco por cento. Usamos pytest para testar casos válidos, inválidos e limites como 59 e 60 anos. Agora vou executar os testes."  
Comando: `python -m pytest -v`.

## Livia Ayumi — Banco e migrações
"Persistimos aprovados e rejeitados no SQLite. Para evoluir a coluna cliente sem quebrar a aplicação, usamos Expand-Contract. Primeiro adicionamos primeiro_nome e sobrenome. Depois fazemos Dual Write e Backfill. Por último, após garantir compatibilidade, removemos a coluna antiga. Os testes comprovam a leitura e a gravação antes, durante e depois da mudança."

## Mariana Melendez — CI/CD
"Configuramos GitHub Actions para executar a cada push e pull request para main. O pipeline instala Python, roda testes, migra o banco, executa o processamento e verifica os resultados. Um pull request com falha de teste aparece com check vermelho; com testes aprovados, o check fica verde. A regra de bloqueio do merge deve ser configurada no GitHub caso desejemos impedir merges sem aprovação."  
Mostrar o workflow e um PR real depois de publicar o projeto.

## João Gabriel Alves — Observabilidade e encerramento
"Agora vamos executar a aplicação. O arquivo app.log registra INFO para aprovações, WARNING para rejeições e ERROR para falhas de execução. O resumo mostra dez transações, sete aprovadas, três rejeitadas e o tempo em milissegundos. Com isso demonstramos testes, evolução segura de banco, integração contínua e observabilidade."  
Comando: `python main.py --banco apresentacao.db --log app.log`.

## Perguntas prováveis

**Por que são 3 rejeitadas?** Valor negativo, CPF curto e valor zero.  
**O que é Dual Write?** Gravar simultaneamente o nome antigo e os novos campos durante a transição.  
**O que é Backfill?** Atualizar os registros antigos para preencher as novas colunas.  
**O que o CI faz?** Valida automaticamente o projeto a cada push/PR no ramo main.  
**Como medir o tempo?** Com `time.perf_counter()`, convertendo segundos em milissegundos.
