async function loadComments() {
    try {
        const response = await fetch('/comments');
        const comments = await response.json();
        const list = document.getElementById('comments-list');
        list.innerHTML = '';
        comments.forEach(c => {
            const li = document.createElement('li');
            li.className = 'comment-item';

            const span = document.createElement('span');
            span.className = 'comment-text';
            span.textContent = c.text;
            li.appendChild(span);

            const actions = document.createElement('span');
            actions.className = 'comment-actions';

            const editBtn = document.createElement('button');
            editBtn.textContent = 'Edit';
            editBtn.onclick = () => editComment(c.id, c.text);
            actions.appendChild(editBtn);

            const delBtn = document.createElement('button');
            delBtn.textContent = 'Delete';
            delBtn.onclick = () => deleteComment(c.id);
            actions.appendChild(delBtn);

            li.appendChild(actions);
            list.appendChild(li);
        });
    } catch (err) {
        console.error('Failed to load comments', err);
    }
}

async function addComment(text) {
    const res = await fetch('/comments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
    });
    if (res.ok) {
        loadComments();
    }
}

async function editComment(id, currentText) {
    const newText = prompt('Edit comment', currentText);
    if (newText !== null) {
        const res = await fetch(`/comments/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: newText })
        });
        if (res.ok) {
            loadComments();
        }
    }
}

async function deleteComment(id) {
    const res = await fetch(`/comments/${id}`, {
        method: 'DELETE'
    });
    if (res.ok) {
        loadComments();
    }
}

document.getElementById('comment-form').addEventListener('submit', e => {
    e.preventDefault();
    const input = document.getElementById('comment-input');
    const text = input.value.trim();
    if (text) {
        addComment(text);
        input.value = '';
    }
});

window.onload = loadComments;
