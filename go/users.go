package main

import "fmt"

func init() {
	RegisterAction("users/create_user", CreateUser{})
	RegisterAction("users/update_password", UpdatePassword{})
}

// CreateUser is a action to creates a user object
type CreateUser struct{}

// Validate validates that the payload of CreateUser is correct
func (cu CreateUser) Validate(allData *AllDataType, payload map[string]interface{}) error {
	username, ok := payload["username"]
	if !ok {
		return fmt.Errorf("create user action needs a username")
	}
	for _, userElement := range allData.Database["users/user"] {
		if userElement["username"] == username {
			return fmt.Errorf("username `%s` already exists", username)
		}
	}
	return nil
}

// Execute creates a new user object.
func (cu CreateUser) Execute(allData *AllDataType, payload map[string]interface{}) (map[string]interface{}, error) {
	user := make(map[string]interface{})
	user["username"] = payload["username"]
	user["created"] = payload["current_time"]
	user["last_updated"] = payload["current_time"]
	userID := allData.addElement("users/user", user)
	returnValue := make(map[string]interface{})
	returnValue["id"] = userID
	return returnValue, nil
}

// UpdatePassword is an action to sets a new password to a user object.
type UpdatePassword struct{}

// Validate validates the payload of the UpdatePassword action.
func (up UpdatePassword) Validate(allData *AllDataType, payload map[string]interface{}) error {
	if _, ok := payload["password"]; !ok {
		return fmt.Errorf("update_passwod needs a password")
	}
	userIDValue, ok := payload["id"]
	if !ok {
		return fmt.Errorf("update_passwod needs a user id")
	}
	userID, ok := userIDValue.(float64) // golangs json encoder uses float64 for numbers
	if !ok {
		return fmt.Errorf("user id has to be an int not  %T", userIDValue)
	}
	if _, ok := allData.Database["users/user"][int(userID)]; !ok {
		return fmt.Errorf("User with id `%d` does not exist", int(userID))
	}
	return nil
}

// Execute of UpdatePassword sets the new password of an user
func (up UpdatePassword) Execute(allData *AllDataType, payload map[string]interface{}) (map[string]interface{}, error) {
	userID := int(payload["id"].(float64))
	user := allData.Database["users/user"][userID]
	user["password"] = payload["password"]
	user["last_updated"] = payload["current_time"]
	returnValue := make(map[string]interface{})
	allData.ChangedElements = append(allData.ChangedElements, ElementID{"users/user", userID})
	return returnValue, nil
}
