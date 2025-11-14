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
        message.textContent = "Please paste in your club's mailing list with @lakesideschool.org included. (This can be done by copying the To: line on past emails from Outlook.)";
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
                newMembers = JSON.parse(this.responseText);
                message.textContent = "Success!";
                textBox.value = "";
                textBox.style.display = "";
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

function copyUsers(users, button) {
    clipboard = "";
    users.forEach(
        function(user) {
            clipboard += user.email + "\; ";
        }
    );
    navigator.clipboard.writeText(clipboard); // https://developer.mozilla.org/en-US/docs/Web/API/Clipboard/writeText
    button.textContent = "Copied!";
}

function addLeader(club_id, member_id, button) {
    button.parentElement.parentElement.remove()

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

function kickMember(club_id, member_id, button) {
    button.parentElement.parentElement.remove()
    
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

function showMembershipActions(node) {
    const membershipActions = node.getElementsByClassName("membership-action");
    Array.from(membershipActions).forEach(membership_action => {
        membership_action.style.visibility = "visible";
    });
}

function hideMembershipActions(node) {
    const membershipActions = node.getElementsByClassName("membership-action");
    Array.from(membershipActions).forEach(membership_action => {
        membership_action.style.visibility = "hidden";
    });
}