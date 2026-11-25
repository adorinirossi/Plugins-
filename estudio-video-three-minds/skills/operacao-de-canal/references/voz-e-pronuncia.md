# Voz e pronúncia do canal

A voz é marca: uma voz só, mesmo ritmo, mesma pronúncia, em todos os vídeos. Voz plana ou rápida demais é das primeiras causas de abandono em canal sem rosto. Para configurar ou clonar a voz, usar a skill de configuração de voz da conta (ElevenLabs ou motor local); este arquivo trata do controle de qualidade contínuo.

## Configuração fixa (registrar na ficha)
- Voz (ID), modelo, idioma PT-BR
- Velocidade: começar ~10% abaixo do padrão da ferramenta (vozes de IA tendem a ler rápido demais para retenção); ajustar pelo teste de escuta
- Estabilidade/expressividade: moderada — ênfase nas palavras-chave, sem teatralidade
- Pausas: vírgula curta; ponto médio; quebra de bloco = pausa longa (usar marcações de pausa da ferramenta quando houver)

## Glossário de pronúncia — `canal-<slug>/glossario-pronuncia.csv`
```
termo,como_escrever_para_a_voz,observacao
Foucault,Fucô,
Weber,Véber,sociólogo alemão
RedVelvet,Réd Vélvet,pronúncia inglesa
séc. XIX,século dezenove,
```
- Antes de gerar a narração, substituir no texto enviado à voz (não na legenda) os termos do glossário.
- Números, siglas, datas e abreviações são escritos por extenso para a voz.
- Termo novo duvidoso (nome próprio estrangeiro, termo técnico): pesquisar a pronúncia e acrescentar ao glossário antes de gerar.

## Escuta obrigatória (cada narração)
- [ ] Ouvida inteira antes da montagem
- [ ] Nenhum nome ou termo pronunciado errado
- [ ] Ritmo ~2,3–2,5 palavras/s; sem atropelo nas listas
- [ ] Ênfase cai na palavra certa do gancho
- [ ] Sem ruído, clique, respiração artificial ou corte de sílaba
Erro encontrado → corrigir glossário/texto e regenerar só o trecho. Registrar o termo no glossário para não repetir.
