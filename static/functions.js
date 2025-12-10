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
    const clipboard = (members || []).map((member) => member.email).join("; ");
    navigator.clipboard.writeText(clipboard || "");
    updateTooltip("Copied!", button);
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
    button.dataset.meetingId = meeting.id;
    button.addEventListener('click', () => joinMeeting(meeting.id, button));

    meetingsList.insertBefore(copy, template.nextSibling);
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.join-club-button').forEach((button) => {
        const clubId = button.dataset.clubId;
        const authenticated = button.dataset.authenticated === 'True';
        button.addEventListener('click', () => joinClub(clubId, authenticated, button));
    });

    document.querySelectorAll('.leave-club-button').forEach((button) => {
        const clubId = button.dataset.clubId;
        button.addEventListener('click', () => leaveClub(clubId, button));
    });

    document.querySelectorAll('.join-meeting-button').forEach((button) => {
        const meetingId = button.dataset.meetingId;
        button.addEventListener('click', () => joinMeeting(meetingId, button));
    });

    document.querySelectorAll('.leave-meeting-button').forEach((button) => {
        const meetingId = button.dataset.meetingId;
        button.addEventListener('click', () => leaveMeeting(meetingId, button));
    });

    const importUsersButton = document.getElementById('import-user-button');
    if (importUsersButton) {
        importUsersButton.addEventListener('click', () => {
            importUsers(importUsersButton.dataset.clubId);
        });
    }

    document.querySelectorAll('[data-action="copy-users"]').forEach((button) => {
        const clubId = button.dataset.clubId;
        button.addEventListener('mouseleave', () => {
            updateTooltip("Copy Emails", button);
        });
        button.addEventListener('click', () => {
            copyUsers(clubId, button);
        });
    });

    document.querySelectorAll('.club-user-list').forEach((listElement) => {
        listElement.addEventListener('click', (event) => {
            const actionTarget = event.target.closest('[data-action]');
            if (!actionTarget || !listElement.contains(actionTarget)) {
                return;
            }
            const actionWrapper = actionTarget.closest('.membership-action');
            if (actionWrapper && actionWrapper.classList.contains('action-hidden')) {
                return;
            }
            const action = actionTarget.dataset.action;   
            const clubId = listElement.dataset.clubId;
            const memberId = actionTarget.dataset.memberId;
            if (action === "add-leader") {
                addLeader(clubId, memberId, actionTarget);
            } else if (action === "kick-member") {
                kickMember(clubId, memberId, actionTarget);
            } else if (action === "demote-leader") {
                demoteLeader(clubId, memberId, actionTarget);
            } else if (action === "copy-email") {
                navigator.clipboard.writeText(actionTarget.dataset.email);
                return;
            }
        });
    });

    const newMeetingForm = document.getElementById('new-meeting-card');
    if (newMeetingForm) {
        newMeetingForm.addEventListener('submit', (event) => {
            event.preventDefault(); // prevent sending form regularly
            createMeeting(newMeetingForm);
        });
    }
});
