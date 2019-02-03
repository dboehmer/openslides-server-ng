package main

import (
	"fmt"
)

// ActionData contains a name of an action and the payload to call it.
type ActionData struct {
	Action  string                 `json:"action"`
	Payload map[string]interface{} `json:"payload"`
}

// Action implements methods to check the payload and executes in on the
// database.
type Action interface {
	Validate(allData *AllDataType, payload map[string]interface{}) error
	Execute(allData *AllDataType, payload map[string]interface{}) (map[string]interface{}, error)
}

var allActions map[string]Action

func init() {
	allActions = make(map[string]Action)
}

// RegisterAction registers an Action interface
func RegisterAction(name string, action Action) {
	allActions[name] = action
}

// GetAction return an Action for a name
func GetAction(name string) (Action, error) {
	action, ok := allActions[name]
	if !ok {
		return nil, fmt.Errorf("action with name `%s` does not exist", name)
	}
	return action, nil

}

func prepareActions(actionDataList []ActionData, currentTime int64) {
	// TODO: Add request_user
	for _, actionData := range actionDataList {
		actionData.Payload["current_time"] = currentTime
	}
}

func handleActions(actionDataList []ActionData) (*AllDataType, []map[string]interface{}, error) {
	databaseWriteLock.Lock()
	defer databaseWriteLock.Unlock()

	allData := getAllData()
	returnValues := make([]map[string]interface{}, 0)

	for _, actionData := range actionDataList {
		debug(
			fmt.Sprintf(
				"handle action %s with payload %s",
				actionData.Action,
				actionData.Payload,
			),
		)
		action, err := GetAction(actionData.Action)
		if err != nil {
			return nil, nil, err
		}
		err = action.Validate(allData, actionData.Payload)
		if err != nil {
			return nil, nil, err
		}
		returnValue, err := action.Execute(allData, actionData.Payload)
		if err != nil {
			return nil, nil, err
		}
		returnValues = append(returnValues, returnValue)
	}
	if err := saveDatabase(allData); err != nil {
		return nil, nil, err
	}
	return allData, returnValues, nil
}
