package main

// InformChangedElements informs all clients about changeld elements
func InformChangedElements(allData *AllDataType) {
	changed := make(map[string][]interface{})
	deleted := make(map[string][]int)
	for _, ElementID := range allData.ChangedElements {
		element, ok := allData.Database[ElementID.Collection][ElementID.ID]
		if ok {
			changed[ElementID.Collection] = append(changed[ElementID.Collection], element)
		} else {
			deleted[ElementID.Collection] = append(deleted[ElementID.Collection], ElementID.ID)
		}
	}
	SendToAll(AutoupdateMessage{
		Type:    "autoupdate",
		Changed: changed,
		Deleted: deleted,
		AllData: false,
	})
}
