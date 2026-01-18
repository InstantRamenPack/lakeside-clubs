function joinClub(club_id, authenticated, button) {
    if (!authenticated) {
        window.location.href = "/joinClub?club_id=" + club_id;
        return;
    }
    const targetButton = button.tagName === 'BUTTON' ? button : button.closest('button');
    targetButton.dataset.action = "leave-club";
    updateButton("Leave Club", targetButton, "logout");

    fetch("/joinClub", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: "club_id=" + encodeURIComponent(club_id),
    }).catch(() => {});
}

function leaveClub(club_id, button) {
    const targetButton = button.tagName === 'BUTTON' ? button : button.closest('button');
    targetButton.dataset.action = "join-club";
    updateButton("Join Club", targetButton, "login");
	
    fetch("/leaveClub", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: "club_id=" + encodeURIComponent(club_id),
    }).catch(() => {});
}

function importUsers(club_id) {
    const message = document.getElementById("import-user-message");
    const textBox = document.getElementById("import-user-text");
    const button = document.getElementById("import-user-button");
    const wrapper = button.closest('button');

    if (textBox.style.display == "none" || textBox.style.display == "") {
        textBox.style.display = "block";
        message.style.display = "block";
        updateButton("Submit!", button);
        return;
    } else {
        updateButton("Submitting...", button);
        if (wrapper) wrapper.disabled = true;
    }

    const body = "data=" + encodeURIComponent(textBox.value) + "&club_id=" + encodeURIComponent(club_id);
    fetch("/importUsers", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body,
    })
        .then((response) => {
            if (!response.ok) {
                return null;
            }
            return response.json();
        })
        .then((payload) => {
            if (!payload) {
                return;
            }
            const newMembers = payload.new_members || [];
            const renderedMembers = payload.rendered_members || [];
            if (newMembers.length == 0) {
                message.textContent = "No new users imported.";
            } else {
                message.textContent = "Imported " + newMembers[0].email.slice(0, -19);
                if (newMembers.length == 1) {
                    message.textContent += "."
                } else if (newMembers.length == 2) {
                    message.textContent += " and " + newMembers[1].email.slice(0, -19) + ".";
                } else {
                    for (let i = 1; i < newMembers.length - 1; i++) {
                        message.textContent += ", " + newMembers[i].email.slice(0, -19);
                    }
                    message.textContent += ", and " + newMembers[newMembers.length - 1].email.slice(0, -19) + ".";
                }
            }

            const memberList = document.getElementById("club-member-list");
            renderedMembers.forEach((memberHtml) => {
                memberList.insertAdjacentHTML("beforeend", memberHtml);
            });
            attachTooltips();

            textBox.value = "";
            textBox.style.display = "";
            if (wrapper) wrapper.disabled = false;
            updateButton("Import Users", button);
        })
        .catch(() => {});
}

function setActionVisibility(entry, actionName, visible) {
    const action = entry.querySelector(`[data-action="${actionName}"]`);
    if (!action) {
        return;
    }
    const wrapper = action.closest('.membership-action');
    if (wrapper) {
        wrapper.style.display = visible ? "" : "none";
    }
}

function showActions(entry, type) {
    if (type === "leader") {
        setActionVisibility(entry, 'add-leader', false);
        setActionVisibility(entry, 'kick-member', false);
        setActionVisibility(entry, 'demote-leader', true);
    } else if (type === "member") {
        setActionVisibility(entry, 'add-leader', true);
        setActionVisibility(entry, 'kick-member', true);
        setActionVisibility(entry, 'demote-leader', false);
    }
}

function fetchMembers(club_id) {
    // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/async_function
    return new Promise((resolve) => {
        fetch("/fetchMembers", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: "club_id=" + encodeURIComponent(club_id),
        })
            .then((response) => {
                if (!response.ok) {
                    return null;
                }
                return response.json();
            })
            .then((payload) => {
                if (payload === null) {
                    return;
                }
                resolve(payload);
            })
            .catch(() => {});
    });
}

async function copyUsers(club_id, button) {
    updateButton("Copying...", button);
    const members = await fetchMembers(club_id);
    navigator.clipboard.writeText((members).map((member) => member.email).join("; "));
    updateButton("Copied!", button);
}

async function constructEmail(club_id) {
    const members = await fetchMembers(club_id);
    
    let url = "https://outlook.office.com/mail/deeplink/compose?to=";
    let bccStart = false;
    for (let i = 0; i < members.length; i++) {
        if (!bccStart && members[i].is_leader == 0) {
            bccStart = true;
            url = url.substring(0, url.length - 1);
            // not sure why but Outlook requires ? not &
            url += "?bcc=";
        }
        url += members[i].email + ";";
    }
    url = url.substring(0, url.length - 1);

    return url;
}

async function emailClub(club_id, button) {
    updateButton("Opening Outlook...", button);
    const url = await constructEmail(club_id);
    updateButton("Send Email", button);
    window.open(url);
}

async function emailMeeting(button) {
    updateButton("Opening Outlook...", button);
    clubId = button.dataset.clubId;
    title = button.dataset.meetingTitle;
    description = button.dataset.meetingDescription;
    let url = await constructEmail(clubId);
    url += "&subject=" + title + "&body=" + description;
    updateButton("Email Meeting", button);
    window.open(url);
}

function addLeader(club_id, user_id, button) {
    const entry = button.closest('li');
    const leaderList = document.getElementById("club-leader-list");
    leaderList.appendChild(entry);
    showActions(entry, "leader");
    attachTooltips();

    fetch("/addLeader", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: "club_id=" + encodeURIComponent(club_id) + "&user_id=" + encodeURIComponent(user_id),
    }).catch(() => {});
}

function demoteLeader(club_id, user_id, button) {
    const entry = button.closest('li');
    const memberList = document.getElementById("club-member-list");
    memberList.insertBefore(entry, memberList.children[0]);
    showActions(entry, "member");
    attachTooltips();

    fetch("/demoteLeader", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: "club_id=" + encodeURIComponent(club_id) + "&user_id=" + encodeURIComponent(user_id),
    }).catch(() => {});
}

function kickMember(club_id, user_id, button) {
    button.parentElement.remove()
    
    fetch("/kickMember", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: "club_id=" + encodeURIComponent(club_id) + "&user_id=" + encodeURIComponent(user_id),
    }).catch(() => {});
}

function deleteMeeting(meeting_id, club_id, button) {
    if (!confirm("Are you sure you want to delete this meeting? This action is irreversible, no I cannot resurrect your meeting.")) {
        return;
    }

    button.closest('.meeting-card').remove();

    fetch("/deleteMeeting", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: "meeting_id=" + encodeURIComponent(meeting_id) + "&club_id=" + encodeURIComponent(club_id),
    }).catch(() => {});
}

function parseTimeToMinutes(value) {
    const parts = value.split(':');
    if (parts.length !== 2) {
        return NaN;
    }
    return Number(parts[0]) * 60 + Number(parts[1]);
}

function validateMeetingForm(form, isMeeting) {
    clearWarnings(form);
    let valid = true;
    const requiredMessage = isMeeting ? "Required for meetings." : "Required.";
    const setWarning = (element, message) => {
        if (!element) {
            return;
        }
        element.dataset.warning = message;
        valid = false;
    };

    const titleInput = form.elements.namedItem('title');
    if (!titleInput || !titleInput.value.trim()) {
        setWarning(titleInput, requiredMessage);
    } else {
        // if both title and description show it's kind of cluttered
        const descriptionInput = form.elements.namedItem('description');
        if (!descriptionInput || !descriptionInput.value.trim()) {
            setWarning(descriptionInput, requiredMessage);
        }
    }

    if (!isMeeting) {
        if (!valid) {
            attachWarnings(form);
        }
        return valid;
    }

    // remaining is meeting-specific
    const dateInput = form.elements.namedItem('date');
    if (!dateInput.value) {
        setWarning(dateInput, requiredMessage);
    } else {
        // cast to date
        const selected = new Date(`${dateInput.value}T00:00:00`);
        const today = new Date();
        // set hour to midnight so time-of-day doesn't affect result
        today.setHours(0, 0, 0, 0);
        if (selected < today) {
            setWarning(dateInput, "Date must be today or later.");
        }
    }
    const startInput = form.elements.namedItem('start-time');
    const endInput = form.elements.namedItem('end-time');
    if (!startInput.value || !endInput.value) {
        setWarning(endInput.parentNode, requiredMessage);
    }
    if (startInput.value && endInput.value) {
        const startMinutes = parseTimeToMinutes(startInput.value);
        const endMinutes = parseTimeToMinutes(endInput.value);
        if (!Number.isNaN(startMinutes) && !Number.isNaN(endMinutes) && endMinutes <= startMinutes) {
            setWarning(endInput.parentNode, "End time must be after start time.");
        }
    }

    const locationInput = form.elements.namedItem('location');
    if (!locationInput.value) {
        setWarning(locationInput, requiredMessage);
    }

    if (!valid) {
        attachWarnings(form);
    }
    return valid;
}

// https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Forms/Sending_forms_through_JavaScript
function createMeeting(form, submitter) {
    const submitButtons = Array.from(form.querySelectorAll('input[type="submit"]'));
    const action = submitter && submitter.dataset.action ? submitter.dataset.action : "create-meeting";
    const isMeeting = action !== "create-annnouncement";
    const submitLabel = submitter ? submitter.value : "Create Meeting";

    if (!validateMeetingForm(form, isMeeting)) {
        return;
    }

    const payload = new URLSearchParams(new FormData(form));
    payload.append('club_id', form.dataset.clubId);
    payload.append('is_meeting', isMeeting ? '1' : '0');
    payload.append('action', action);
    if (!isMeeting) {
        payload.delete('date');
        payload.delete('start-time');
        payload.delete('end-time');
        payload.delete('location');
    }

    submitter.value = "Creating...";
    submitButtons.forEach((button) => {
        button.disabled = true;
    });

    fetch("/createMeeting", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: payload.toString(),
    })
        .then((response) => {
            if (!response.ok) {
                submitter.value = "Oops! Try again.";
                return null;
            }
            return response.json();
        })
        .then((responsePayload) => {
            if (!responsePayload) {
                return;
            }
            submitter.value = submitLabel;
            form.reset();

            const isMeetingPost = responsePayload.is_meeting === true || responsePayload.is_meeting === 1 || responsePayload.is_meeting === "1";
            const panelId = isMeetingPost ? 'club-meetings-panel' : 'club-announcements-panel';
            const postsPanel = document.getElementById(panelId);
            const cardHtml = responsePayload.html || "";

            if (cardHtml && postsPanel) {
                postsPanel.insertAdjacentHTML('afterbegin', cardHtml);
                attachTooltips();
            }

            setActiveTab(document.querySelector(`.tab-bar [data-tab-target="${panelId}"]`).closest('.tab-bar'), panelId);
            if (isMeetingPost) {
                const noMeetings = document.querySelector('#no-meetings');
                if (noMeetings) {
                    noMeetings.remove();
                }
            } else {
                const noAnnouncements = document.querySelector('#no-announcements');
                if (noAnnouncements) {
                    noAnnouncements.remove();
                }
            } 
        })
        .catch(() => {
            submitter.value = "Oops! Try again.";
        })
        .finally(() => {
            submitButtons.forEach((button) => {
                button.disabled = false;
            });
        });
}

function startCreateTag(control) {
    const addButton = control.querySelector('[data-action="start-create-tag"]');
    const input = control.querySelector('input[name="new-tag"]');
    const saveButton = control.querySelector('[data-action="create-tag"]');

    addButton.style.display = "none";
    input.style.display = "inline-block";
    saveButton.style.display = "inline";
    input.focus();
}

function createTag(control) {
    const addButton = control.querySelector('[data-action="start-create-tag"]');
    const input = control.querySelector('input[name="new-tag"]');
    const tagName = input.value.trim();
    const clubId = control.dataset.clubId;

    const saveButton = control.querySelector('[data-action="create-tag"]');
    saveButton.textContent = "progress_activity";
    saveButton.style.display = "inline";
    saveButton.classList.add("spin");

    fetch("/createTag", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: "club_id=" + encodeURIComponent(clubId) + "&tag_name=" + encodeURIComponent(tagName),
    })
        .then((response) => {
            if (!response.ok) {
                return null;
            }
            return response.json();
        })
        .then((tag) => {
            if (!tag) {
                return;
            }
            saveButton.classList.remove("spin");

            const template = document.getElementById("club-tag-template");

            const copy = template.content.cloneNode(true);
            copy.querySelector(".club-tag").dataset.tagId = tag.tag_id;
            copy.querySelector(".tag-name").textContent = tag.name;
            const deleteAction = copy.querySelector('[data-action="delete-tag"]');
            deleteAction.dataset.tagId = tag.tag_id;
            deleteAction.dataset.clubId = clubId;

            const insertionPoint = document.querySelector(".create-tag-control");
            document.getElementById("club-tags").insertBefore(copy, insertionPoint);
            attachTooltips();

            addButton.style.display = "";
            input.value = "";
            input.style.display = "none";
            saveButton.textContent = "check";
            saveButton.style.display = "none";
        })
        .catch(() => {});
}

function deleteTag(tagId, clubId, button) {
    button.closest(".club-tag").remove();

    fetch("/deleteTag", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: "club_id=" + encodeURIComponent(clubId) + "&tag_id=" + encodeURIComponent(tagId),
    }).catch(() => {});
}

document.addEventListener('DOMContentLoaded', () => {
    // https://developer.mozilla.org/en-US/docs/Web/API/Element/click_event
    document.addEventListener('click', (event) => {
        const actionTarget = event.target.closest('[data-action]');
        if (!actionTarget) {
            return;
        }
        const action = actionTarget.dataset.action;

        switch (action) {
            case "join-club": {
                const clubId = actionTarget.dataset.clubId;
                const authenticated = actionTarget.dataset.authenticated === 'True';
                joinClub(clubId, authenticated, actionTarget);
                break;
            }
            case "leave-club": {
                leaveClub(actionTarget.dataset.clubId, actionTarget);
                break;
            }
            case "delete-meeting": {
                deleteMeeting(actionTarget.dataset.meetingId, actionTarget.dataset.clubId, actionTarget);
                break;
            }
            case "import-users": {
                importUsers(actionTarget.dataset.clubId);
                break;
            }
            case "copy-users": {
                copyUsers(actionTarget.dataset.clubId, actionTarget);
                break;
            }
            case "send-email": {
                emailClub(actionTarget.dataset.clubId, actionTarget);
                break;
            }
            case "email-meeting": {
                emailMeeting(actionTarget);
                break;
            }
            case "add-leader": {
                const listElement = actionTarget.closest('.club-user-list');
                addLeader(listElement.dataset.clubId, actionTarget.dataset.userId, actionTarget);
                break;
            }
            case "kick-member": {
                const listElement = actionTarget.closest('.club-user-list');
                kickMember(listElement.dataset.clubId, actionTarget.dataset.userId, actionTarget);
                break;
            }
            case "demote-leader": {
                const listElement = actionTarget.closest('.club-user-list');
                demoteLeader(listElement.dataset.clubId, actionTarget.dataset.userId, actionTarget);
                break;
            }
            case "copy-email": {
                navigator.clipboard.writeText(actionTarget.dataset.email);
                break;
            }
            case "delete-tag": {
                const tagElement = actionTarget.closest('.club-tag');
                const tagsContainer = actionTarget.closest('#club-tags');
                deleteTag(tagElement.dataset.tagId, tagsContainer.dataset.clubId, actionTarget);
                break;
            }
            case "start-create-tag": {
                const control = actionTarget.closest('.create-tag-control');
                startCreateTag(control);
                break;
            }
            case "create-tag": {
                const control = actionTarget.closest('.create-tag-control');
                createTag(control);
                break;
            }
            default:
                break;
        }
    });

    const newMeetingForm = document.getElementById('new-meeting-card');
    if (newMeetingForm) {
        newMeetingForm.addEventListener('submit', (event) => {
            event.preventDefault(); // prevent sending form regularly
            createMeeting(newMeetingForm, event.submitter);
        });
    }
});
