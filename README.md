# pybrd

Robô oficial da Python Brasil no Discord

## Autenticação

O `AuthenticationCog` é responsável pelo credenciamento dos participantes da Python Brasil no Discord. O *cog* é genérico suficiente para funcionar com diferentes provedores, mas até agora apenas Eventbrite foi implementado.

**Eventbrite**

Eventbrite não possui uma API para conferir se uma pessoa está inscrita ou não no evento, além de não poder também marcar os participantes como credenciados na plataforma. Portanto, para credenciar os participantes do evento, começamos listando todos os participantes do evento (API disponível), criamos um *cache* local e, a partir daí, conseguimos verificar os participantes. Uma tarefa agendada é responsável por atualizar o *cache* local a cada 5 minutos.