function joinClub(club_id, authenticated, button) {
    if (!authenticated) {
        window.location.href = "/joinClub?id=" + club_id;
        return;
    }
	button.textContent = "Joined!"; // illusion of responsiveness
    button.disabled = true;
	
	const xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function() {
		if (this.readyState == 4) {
            if (this.status == 200) {
                button.textContent = "Joined!";
            } else {
                button.textContent = "Oops! Try again.";
            }
		}
    };
	
	xhttp.open("POST", "/joinClub", true);
    xhttp.setRequestHeader("Content-Type", "application/x-www-form-urlencoded"); 
    xhttp.send("id=" + encodeURIComponent(club_id));
}

function leaveClub(club_id, button) {
	button.textContent = "Club left!"; // illusion of responsiveness
    button.disabled = true;
	
	const xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function() {
		if (this.readyState == 4) {
            if (this.status == 200) {
                button.textContent = "Club left!";
            } else {
                button.textContent = "Oops! Try again.";
            }
		}
    };
	
	xhttp.open("POST", "/leaveClub", true);
    xhttp.setRequestHeader("Content-Type", "application/x-www-form-urlencoded"); 
    xhttp.send("id=" + encodeURIComponent(club_id));
}

function importUsers(club_id) {
    const message = document.getElementById("import-user-message");
    const textBox = document.getElementById("import-user-text");
    const button = document.getElementById("import-user-button");

    if (textBox.style.display == "none" || textBox.style.display == "") {
        textBox.style.display = "block";
        message.style.display = "block";
        button.textContent = "Submit!";
        return;
    } else {
        button.textContent = "Submitting...";
        button.disabled = true;
    }

    const xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4) {
            if (this.status == 200) {
                const newMembers = JSON.parse(this.responseText);
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
                const template = memberList.getElementsByTagName("template")[0];
                newMembers.forEach((user) => {
                    appendMember(template, user);
                });
                attachTooltips();

                textBox.value = "";
                textBox.style.display = "";
                button.disabled = false;
                button.textContent = "Import Users";
            } else {
                message.textContent = "Error, please try again.";
            }
        }
    }

    xhttp.open("POST", "/importUsers", true);
    xhttp.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
    xhttp.send("data=" + encodeURIComponent(textBox.value) + "&id=" + encodeURIComponent(club_id));
}

function appendMember(template, user) {
    const copy = template.content.cloneNode(true);
    copy.querySelector(".user-name").textContent = user.email.slice(0, -19);
    const actionButtons = copy.querySelectorAll("[data-action]");
    actionButtons.forEach((actionButton) => {
        if (actionButton.dataset.action === "copy-email") {
            actionButton.dataset.email = user.email;
            const tooltipWrapper = actionButton.parentElement;
            if (tooltipWrapper) {
                tooltipWrapper.dataset.tooltip = user.email;
            }
            return;
        }
    });

    showMemberActions(copy);
    template.parentNode.appendChild(copy);
}

function setActionVisibility(entry, actionName, visible) {
    const action = entry.querySelector(`[data-action="${actionName}"]`);
    if (!action) {
        return;
    }
    const wrapper = action.closest('.membership-action');
    if (wrapper) {
        wrapper.classList.toggle('action-hidden', !visible);
    }
}

function showLeaderActions(entry) {
    setActionVisibility(entry, 'add-leader', false);
    setActionVisibility(entry, 'kick-member', false);
    setActionVisibility(entry, 'demote-leader', true);
}

function showMemberActions(entry) {
    setActionVisibility(entry, 'add-leader', true);
    setActionVisibility(entry, 'kick-member', true);
    setActionVisibility(entry, 'demote-leader', false);
}

function fetchMembers(club_id) {
    // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/async_function
    return new Promise((resolve) => {
        const xhttp = new XMLHttpRequest();
        xhttp.onreadystatechange = function() {
            if (this.readyState === 4) {
                if (this.status === 200) {
                    resolve(JSON.parse(this.responseText));
                }
            }
        };

        xhttp.open("POST", "/fetchMembers", true);
        xhttp.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
        xhttp.send("id=" + encodeURIComponent(club_id));
    });
}

async function copyUsers(club_id, button) {
    updateTooltip("Copying...", button);
    const members = await fetchMembers(club_id);
    navigator.clipboard.writeText((members).map((member) => member.email).join("; "));
    updateTooltip("Copied!", button);
}

async function constructEmail(club_id) {
    const members = await fetchMembers(club_id);
    
    let url = "https://outlook.office.com/mail/deeplink/compose?to=";
    let bccStart = false;
    for (let i = 0; i < members.length; i++) {
        if (!bccStart && members[i].membership_type == 0) {
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
    updateTooltip("Opening Outlook...", button);
    const url = await constructEmail(club_id);
    window.open(url);
}

async function emailMeeting(button) {
    updateTooltip("Opening Outlook...", button);
    clubId = button.dataset.clubId;
    title = button.dataset.meetingTitle;
    description = button.dataset.meetingDescription;
    let url = await constructEmail(clubId);
    url += "&subject=" + title + "&body=" + description;
    window.open(url);
}

function addLeader(club_id, member_id, button) {
    const entry = button.closest('li');
    const leaderList = document.getElementById("club-leader-list");
    leaderList.appendChild(entry);
    showLeaderActions(entry);
    attachTooltips();

	const xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function() {
		if (this.readyState == 4) {
            if (this.status == 200) {
                
            }
		}
    };
	
	xhttp.open("POST", "/addLeader", true);
    xhttp.setRequestHeader("Content-Type", "application/x-www-form-urlencoded"); 
    xhttp.send("club_id=" + encodeURIComponent(club_id) + "&user_id=" + encodeURIComponent(member_id));
}

function demoteLeader(club_id, member_id, button) {
    const entry = button.closest('li');
    const memberList = document.getElementById("club-member-list");
    memberList.insertBefore(entry, memberList.children[0]);
    showMemberActions(entry);
    attachTooltips();

	const xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function() {
		if (this.readyState == 4) {
            if (this.status == 200) {
                
            }
		}
    };
	
	xhttp.open("POST", "/demoteLeader", true);
    xhttp.setRequestHeader("Content-Type", "application/x-www-form-urlencoded"); 
    xhttp.send("club_id=" + encodeURIComponent(club_id) + "&user_id=" + encodeURIComponent(member_id));
}

function kickMember(club_id, member_id, button) {
    button.parentElement.remove()
    
	const xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function() {
		if (this.readyState == 4) {
            if (this.status == 200) {
                
            }
		}
    };
	
	xhttp.open("POST", "/kickMember", true);
    xhttp.setRequestHeader("Content-Type", "application/x-www-form-urlencoded"); 
    xhttp.send("club_id=" + encodeURIComponent(club_id) + "&user_id=" + encodeURIComponent(member_id));
}

function joinMeeting(meeting_id, button) {
	button.textContent = "Joined!"; // illusion of responsiveness
    button.disabled = true;
	
	const xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function() {
		if (this.readyState == 4) {
            if (this.status == 200) {
                button.textContent = "Joined!";
            } else {
                button.textContent = "Oops! Try again.";
            }
		}
    };
	
	xhttp.open("POST", "/joinMeeting", true);
    xhttp.setRequestHeader("Content-Type", "application/x-www-form-urlencoded"); 
    xhttp.send("id=" + encodeURIComponent(meeting_id));
}

function leaveMeeting(meeting_id, button) {
	button.textContent = "Meeting left!"; // illusion of responsiveness
    button.disabled = true;
	
	const xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function() {
		if (this.readyState == 4) {
            if (this.status == 200) {
                button.textContent = "Meeting left!";
            } else {
                button.textContent = "Oops! Try again.";
            }
		}
    };
	
	xhttp.open("POST", "/leaveMeeting", true);
    xhttp.setRequestHeader("Content-Type", "application/x-www-form-urlencoded"); 
    xhttp.send("id=" + encodeURIComponent(meeting_id));
}

function deleteMeeting(meeting_id, button) {
    if (!confirm("Are you sure you want to delete this meeting? This action is irreversible, no I cannot resurrect your meeting.")) {
        return;
    }

    button.closest('.meeting-card').remove();

	const xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function() {
		if (this.readyState == 4) {
            if (this.status == 200) {

            }
		}
    };
	
	xhttp.open("POST", "/deleteMeeting", true);
    xhttp.setRequestHeader("Content-Type", "application/x-www-form-urlencoded"); 
    xhttp.send("id=" + encodeURIComponent(meeting_id));
}

// https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Forms/Sending_forms_through_JavaScript
function createMeeting(form) {
    const submitButton = form.querySelector('input[type="submit"]');

    const payload = new URLSearchParams(new FormData(form));
    payload.append('club_id', form.dataset.clubId);

    submitButton.value = "Creating...";
    submitButton.disabled = true;

    const xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4) {
            submitButton.value = "Create Meeting";
            submitButton.disabled = false;
            if (this.status == 200) {
                const meeting = JSON.parse(this.responseText);
                insertMeetingCard(meeting);
                form.reset();
            } else {
                submitButton.value = "Oops! Try again.";
            }
        }
    };

    xhttp.open("POST", "/createMeeting", true);
    xhttp.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
    xhttp.send(payload.toString());
}

function insertMeetingCard(meeting) {
    const meetingsList = document.getElementById('club-meetings-list');
    const template = meetingsList.querySelector('template');

    const copy = template.content.cloneNode(true);
    const card = copy.querySelector('.meeting-card');

    card.querySelector('h2').textContent = meeting.title;
    card.querySelector('.meeting-description').innerHTML = meeting.description;

    const meetingInfo = card.querySelectorAll('.card-info > div');
    meetingInfo[0].querySelector('p').textContent = meeting.date;
    meetingInfo[1].querySelector('p').textContent = meeting.time_range;
    meetingInfo[2].querySelector('p').textContent = meeting.location;

    const button = card.querySelector('button');
    if (button) {
        button.dataset.meetingId = meeting.id;
        button.dataset.action = "join-meeting";
    }

    const emailAction = card.querySelector('[data-action="email-meeting"]');
    emailAction.dataset.meetingId = meeting.id;
    emailAction.dataset.meetingTitle = meeting.title;
    emailAction.dataset.meetingDescription = meeting.description_plain;
    emailAction.dataset.clubId = meeting.club_id;
    emailAction.addEventListener('mouseleave', () => {
        updateTooltip("Email Details", emailAction);
    });

    const deleteAction = card.querySelector('[data-action="delete-meeting"]');
    if (deleteAction) {
        deleteAction.dataset.meetingId = meeting.id;
    }

    meetingsList.insertBefore(copy, template.nextSibling);
}

document.addEventListener('DOMContentLoaded', () => {
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
            case "join-meeting": {
                joinMeeting(actionTarget.dataset.meetingId, actionTarget);
                break;
            }
            case "leave-meeting": {
                leaveMeeting(actionTarget.dataset.meetingId, actionTarget);
                break;
            }
            case "delete-meeting": {
                deleteMeeting(actionTarget.dataset.meetingId, actionTarget);
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
                addLeader(listElement.dataset.clubId, actionTarget.dataset.memberId, actionTarget);
                break;
            }
            case "kick-member": {
                const listElement = actionTarget.closest('.club-user-list');
                kickMember(listElement.dataset.clubId, actionTarget.dataset.memberId, actionTarget);
                break;
            }
            case "demote-leader": {
                const listElement = actionTarget.closest('.club-user-list');
                demoteLeader(listElement.dataset.clubId, actionTarget.dataset.memberId, actionTarget);
                break;
            }
            case "copy-email": {
                navigator.clipboard.writeText(actionTarget.dataset.email);
                break;
            }
            default:
                break;
        }
    });

    document.addEventListener('mouseout', (event) => {
        const actionTarget = event.target.closest('[data-action]');
        if (!actionTarget) {
            return;
        }

        switch (actionTarget.dataset.action) {
            case "copy-users":
                updateTooltip("Copy Emails", actionTarget);
                break;
            case "send-email":
                updateTooltip("Compose in Outlook", actionTarget);
                break;
            case "email-meeting":
                updateTooltip("Email Details", actionTarget);
                break;
            default:
                break;
        }
    });

    const newMeetingForm = document.getElementById('new-meeting-card');
    if (newMeetingForm) {
        newMeetingForm.addEventListener('submit', (event) => {
            event.preventDefault(); // prevent sending form regularly
            createMeeting(newMeetingForm);
        });
    }
});
