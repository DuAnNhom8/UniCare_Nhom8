const getToken = () => sessionStorage.getItem('unicareer_token');
const setToken = value => sessionStorage.setItem('unicareer_token', value);
const logout = () => { sessionStorage.removeItem('unicareer_token'); window.location.href = '/static/index.html'; };
const show = (element, message, error = false) => { element.textContent = message; element.style.display = 'block'; element.classList.toggle('error', error); };
async function api(path, method = 'GET', data = undefined) {
    const headers = {};
    if (getToken()) headers.Authorization = 'Bearer ' + getToken();
    let body;
    if (data instanceof FormData) body = data;
    else if (data !== undefined) { headers['Content-Type'] = 'application/json'; body = JSON.stringify(data); }
    const res = await fetch(path, {method, headers, body});
    let payload;
    const type = res.headers.get('content-type') || '';
    payload = type.includes('application/json') ? await res.json() : await res.text();
    if (!res.ok) {
        const detail = payload && typeof payload === 'object' && payload.detail ? payload.detail : 'Lỗi HTTP ' + res.status;
        throw Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
    }
    return payload;
}
async function currentUser(allowed) {
    if (!getToken()) { window.location.href = '/static/index.html'; throw Error('Chưa đăng nhập'); }
    const me = await api('/auth/me');
    if (allowed && !allowed.includes(me.role)) { window.location.href = '/static/index.html'; throw Error('Không có quyền'); }
    return me;
}
function element(tag, text, className) {
    const result = document.createElement(tag);
    result.textContent = text;
    if (className) result.className = className;
    return result;
}
