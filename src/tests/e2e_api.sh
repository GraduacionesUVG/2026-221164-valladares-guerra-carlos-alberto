#!/bin/bash
# Prueba de extremo a extremo de la API (backend PHP + motor de IA)
# Uso: ./tests/e2e_api.sh [URL_BASE]   (por defecto el backend de docker compose)
B=${1:-http://localhost:8080/api/v1}
J='content-type: application/json'
pass=0; fail=0
check() { if [ "$2" = "$3" ]; then echo "  OK   $1"; pass=$((pass+1)); else echo "  FAIL $1 (esperado $3, obtenido $2)"; fail=$((fail+1)); fi; }
code() { curl -s -o /dev/null -w "%{http_code}" "$@"; }

EMAIL="ana$RANDOM@test.gt"
echo "Registro y autenticación"
R=$(curl -s -XPOST $B/auth/register -H "$J" -d "{\"name\":\"Ana\",\"email\":\"$EMAIL\",\"password\":\"secreto123\"}")
TA=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")
check "registro devuelve token" "$([ -n "$TA" ] && echo si)" "si"
check "registro rol ciudadano" "$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin)['user']['role_id'])")" "2"
check "email duplicado → 400" "$(code -XPOST $B/auth/register -H "$J" -d "{\"name\":\"Ana\",\"email\":\"$EMAIL\",\"password\":\"secreto123\"}")" "400"
check "contraseña corta → 400" "$(code -XPOST $B/auth/register -H "$J" -d '{"name":"X","email":"x@y.gt","password":"123"}')" "400"
check "login incorrecto → 401" "$(code -XPOST $B/auth/login -H "$J" -d "{\"email\":\"$EMAIL\",\"password\":\"mal\"}")" "401"
check "token alterado → 401" "$(code $B/chat/conversations -H "Authorization: Bearer ${TA}x")" "401"
TB=$(curl -s -XPOST $B/auth/login -H "$J" -d '{"email":"user@example.com","password":"password"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")
TADM=$(curl -s -XPOST $B/auth/login -H "$J" -d '{"email":"admin@example.com","password":"password"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")

echo "Conversaciones"
CID=$(curl -s -XPOST $B/chat/conversations -H "Authorization: Bearer $TA" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
check "crear conversación" "$([ -n "$CID" ] && echo si)" "si"
R=$(curl -s -XPOST $B/chat/conversations/$CID/messages -H "$J" -H "Authorization: Bearer $TA" -d '{"content":"¿Cuál es la multa por manejar sin licencia?"}')
echo "     respuesta: $(echo "$R" | python3 -c "import sys,json;d=json.load(sys.stdin)['reply'];print(d['content'][:160].replace(chr(10),' '), '| fuentes:', [s['reference'] for s in d['sources']][:2])")"
check "respuesta con fuentes" "$(echo "$R" | python3 -c "import sys,json;print(len(json.load(sys.stdin)['reply']['sources'])>0)")" "True"
check "mensaje vacío → 400" "$(code -XPOST $B/chat/conversations/$CID/messages -H "$J" -H "Authorization: Bearer $TA" -d '{"content":"  "}')" "400"
check "historial con 2 mensajes" "$(curl -s $B/chat/conversations/$CID/messages -H "Authorization: Bearer $TA" | python3 -c "import sys,json;print([m['role'] for m in json.load(sys.stdin)])")" "['user', 'assistant']"
check "título automático" "$(curl -s $B/chat/conversations -H "Authorization: Bearer $TA" | python3 -c "import sys,json;print(json.load(sys.stdin)[0]['title'][:20])")" "¿Cuál es la multa po"

echo "Aislamiento entre usuarios"
check "otro usuario no ve la conversación → 404" "$(code $B/chat/conversations/$CID/messages -H "Authorization: Bearer $TB")" "404"
check "otro usuario no puede escribir → 404" "$(code -XPOST $B/chat/conversations/$CID/messages -H "$J" -H "Authorization: Bearer $TB" -d '{"content":"hola"}')" "404"
check "otro usuario no puede borrar → 404" "$(code -XDELETE $B/chat/conversations/$CID -H "Authorization: Bearer $TB")" "404"
check "lista de otro usuario sin la conversación" "$(curl -s $B/chat/conversations -H "Authorization: Bearer $TB" | python3 -c "import sys,json;print($CID in [c['id'] for c in json.load(sys.stdin)])")" "False"

echo "Roles"
for ep in /dashboard/stats /users /logs /system/health /documents /rag/config /rag/metrics; do
  check "ciudadano en $ep → 403" "$(code $B$ep -H "Authorization: Bearer $TA")" "403"
  check "admin en $ep → 200" "$(code $B$ep -H "Authorization: Bearer $TADM")" "200"
done
check "admin crea usuario rol inválido → 400" "$(code -XPOST $B/users -H "$J" -H "Authorization: Bearer $TADM" -d '{"name":"X","email":"z@z.gt","password":"secreto123","role_id":7}')" "400"
check "playground admin → 200" "$(code -XPOST $B/rag/playground -H "$J" -H "Authorization: Bearer $TADM" -d '{"content":"requisitos para licencia"}')" "200"
check "endpoint inexistente → 404" "$(code $B/no/existe)" "404"

echo "Datos reales en el panel"
curl -s $B/dashboard/stats -H "Authorization: Bearer $TADM" | python3 -c "import sys,json;d=json.load(sys.stdin);print('     stats:', {k:d[k] for k in ('total_users','total_questions','avg_latency_ms','total_articles','total_documents')}, 'top:', d['top_articles'][:1])"
curl -s $B/logs -H "Authorization: Bearer $TADM" | python3 -c "import sys,json;d=json.load(sys.stdin)['data'][0];print('     log:', d['query'][:40], d['sources'][:2], d['latency_ms'])"
curl -s "$B/system/logs?node=vectordb" -H "Authorization: Bearer $TADM" | python3 -c "import sys,json;print('     vectordb log:', json.load(sys.stdin)['logs'][-1]['message'])"
check "borrar propia conversación" "$(code -XDELETE $B/chat/conversations/$CID -H "Authorization: Bearer $TA")" "200"

echo; echo "Resultado: $pass OK, $fail FALLAS"
[ "$fail" -eq 0 ]
