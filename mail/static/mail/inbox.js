document.addEventListener('DOMContentLoaded', function () {
  // Navigation
  document.querySelector('#inbox').onclick = () => load_mailbox('inbox');
  document.querySelector('#sent').onclick = () => load_mailbox('sent');
  document.querySelector('#archived').onclick = () => load_mailbox('archive');
  document.querySelector('#compose').onclick = compose_email;

  // Send Email
  document.querySelector('#compose-form').onsubmit = send_email;

  // Default
  load_mailbox('inbox');
});

function compose_email() {
  document.querySelector('#emails-view').style.display = 'none';
  document.querySelector('#email-view').style.display = 'none';
  document.querySelector('#compose-view').style.display = 'block';

  document.querySelector('#compose-recipients').value = '';
  document.querySelector('#compose-subject').value = '';
  document.querySelector('#compose-body').value = '';
}

async function send_email(event) {
  event.preventDefault();

  const response = await fetch('/emails', {
    method: 'POST',
    body: JSON.stringify({
      recipients: document.querySelector('#compose-recipients').value,
      subject: document.querySelector('#compose-subject').value,
      body: document.querySelector('#compose-body').value
    })
  });

  const result = await response.json();
    if (response.status === 201) {
      load_mailbox('sent');
  }
}

function load_mailbox(mailbox) {
  document.querySelector('#emails-view').style.display = 'block';
  document.querySelector('#compose-view').style.display = 'none';
  document.querySelector('#email-view').style.display = 'none';

  const view = document.querySelector('#emails-view');
  view.innerHTML = `<h3>${mailbox.charAt(0).toUpperCase() + mailbox.slice(1)}</h3>`;

  fetch(`/emails/${mailbox}`)
    .then(response => response.json())
    .then(emails => {
      emails.forEach(email => {
        const div = document.createElement('div');
        div.className = "list-group-item d-flex justify-content-between";
        div.style.backgroundColor = email.read ? '#f5f5f5' : 'white';
        div.style.cursor = 'pointer';
        div.style.border = '1px solid #ddd';
        div.style.margin = '2px 0';
        
        div.innerHTML = `
          <span><strong>${email.sender}</strong> &nbsp; ${email.subject}</span>
          <span class="text-muted">${email.timestamp}</span>
        `;
        div.onclick = () => view_email(email.id, mailbox);
        view.append(div);
      });
    });
}

function view_email(id, mailbox) {
  document.querySelector('#emails-view').style.display = 'none';
  document.querySelector('#email-view').style.display = 'block';

  fetch(`/emails/${id}`)
    .then(response => response.json())
    .then(email => {
      const view = document.querySelector('#email-view');
      view.innerHTML = `
        <ul class="list-group list-group-flush">
          <li class="list-group-item"><strong>From:</strong> ${email.sender}</li>
          <li class="list-group-item"><strong>To:</strong> ${email.recipients}</li>
          <li class="list-group-item"><strong>Subject:</strong> ${email.subject}</li>
          <li class="list-group-item"><strong>Timestamp:</strong> ${email.timestamp}</li>
        </ul>
        <div class="p-3 border-bottom">${email.body}</div>
        <div class="p-2">
          <button class="btn btn-sm btn-outline-primary" id="reply">Reply</button>
          ${mailbox !== 'sent' ? `<button class="btn btn-sm btn-outline-secondary" id="archive">${email.archived ? 'Unarchive' : 'Archive'}</button>` : ''}
        </div>
      `;

      // Mark as read
      fetch(`/emails/${id}`, { method: 'PUT', body: JSON.stringify({ read: true }) });

      // Archive button logic
      if (mailbox !== 'sent') {
        document.querySelector('#archive').onclick = () => {
          fetch(`/emails/${id}`, { method: 'PUT', body: JSON.stringify({ archived: !email.archived }) })
            .then(() => load_mailbox('inbox'));
        };
      }

      // Reply button logic
      document.querySelector('#reply').onclick = () => {
        compose_email();
        document.querySelector('#compose-recipients').value = email.sender;
        document.querySelector('#compose-subject').value = email.subject.startsWith('Re:') ? email.subject : `Re: ${email.subject}`;
        document.querySelector('#compose-body').value = `On ${email.timestamp} ${email.sender} wrote:\n${email.body}\n\n`;
      };
    });
}