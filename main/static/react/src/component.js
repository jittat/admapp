'use strict';

const e = React.createElement
const { useState, useRef, useEffect } = React
let majors = JSON.parse(document.currentScript.getAttribute('data-majors'))
const Form = () => {
  const [search, setSearch] = useState('')
  const [topics, setTopics] = useState([
    { id: 1, title: 'PAT 1', value: 22, unit: 'หน่วยกิต' },
    { id: 2, title: 'PAT 2', value: 22, unit: 'หน่วยกิต', children: [{ id: 2.1, title: 'PAT 2.2', value: 22, unit: 'หน่วยกิต' }] }])
  const [selectedMajors, setSelectedMajors] = useState([])
  const toggleMajor = (major) => {
    const newSelectedMajors = selectedMajors.slice()
    const index = newSelectedMajors.findIndex((m) => m.id === major.id)
    if (index > -1) {
      newSelectedMajors.splice(index, 1)
    } else {
      newSelectedMajors.push(major)
    }
    setSelectedMajors(newSelectedMajors)
  }
  const addNewTopic = (topic) => {
    const lastTopic = topics.length ? topics[topics.length - 1] : null
    const nextId = lastTopic ? lastTopic.id + 1 : 1
    const newTopic = topics.slice()
    newTopic.push({ id: nextId, title: '', value: '', unit: '' })
    setTopics(newTopic)
  }
  return (
    <div>
      <form>
        <div className="form-group">
          <label htmlFor="majors">เลือกสาขา</label>
          <input
            type="text"
            id="majors"
            className="form-control"
            onKeyUp={(e) => { setSearch((e.target.value).toUpperCase()) }}
            placeholder="ค้นหาชื่อคณะ/สาขา"
          />
          <div className="list-group" style={{ zIndex: 1, height: 300, overflow: 'auto' }}>
            {majors.map(major => {
              const label = major.title
              if (label.toUpperCase().indexOf(search) > -1)
                return (
                  <a
                    href="#"
                    key={major.id}
                    className="list-group-item list-group-item-action"
                    onClick={() => { toggleMajor(major) }}
                  >{label}</a>
                )
            })}
          </div>
        </div>
        {selectedMajors.length > 0 && <table className="table table-bordered">
          <thead>
            <tr>
              <th scope="col">สาขา</th>
              <th scope="col">จำนวนรับ</th>
              <th scope="col"></th>
            </tr>
          </thead>
          <tbody>
            {selectedMajors.map(major => {
              const label = major.title
              return (
                <tr key={`major-${major.id}`}>
                  <td scope="row">{label}</td>
                  <td><input type="number" className="form-control" /></td>
                  <td><button htmltype="button" className="btn btn-secondary" onClick={() => toggleMajor(major)}>ลบ</button></td>
                </tr>
              )
            })}
          </tbody>
        </table>}

        <div className="form-group" >
          <label htmlFor="majors">คุณสมบัติเฉพาะ</label>
          {/* TODO: add known criteria */}
          <table className="table table-bordered">
            <thead>
              <tr>
                <th></th>
                <th></th>
                <th></th>
                <th>หน่วย</th>
              </tr>
            </thead>
            <tbody>
              {topics.map(topic =>
                <PrimaryTopic topic={topic} />
              )}
            </tbody>
          </table>
          <div className="btn btn-primary" onClick={addNewTopic}>+</div>
        </div>
      </form>
    </div>
  )
}
const PrimaryTopic = ({ topic }) => {
  const [secondaryTopics, setSecondaryTopics] = useState([])
  const addNewTopic = () => {
    const newSecondaryTopics = secondaryTopics.slice()
    newSecondaryTopics.push({ id: `${topic.id}.${secondaryTopics.length + 1}`, title: '', value: '', unit: '' })
    console.log(newSecondaryTopics)
    setSecondaryTopics(newSecondaryTopics)
  }
  return (
    <React.Fragment>
      <tr>
        <td>
          {topic.id}
          <div className="btn btn-primary" onClick={addNewTopic}>+</div>
        </td>
        <EditableCell initialValue={topic.title} focusOnMount={true} />
        <EditableCell initialValue={topic.value} />
        <EditableCell initialValue={topic.unit} />
      </tr>
      {secondaryTopics.map(topic => (
        <tr>
          <td>{topic.id}
          </td>
          <EditableCell initialValue={topic.title} focusOnMount={true} />
          <EditableCell initialValue={topic.value} />
          <EditableCell initialValue={topic.unit} />
        </tr>
      ))}
    </React.Fragment>
  )
}
const EditableCell = ({ initialValue, editable = true, focusOnMount = false, children, handleSave, ...restProps }) => {
  const [editing, setEditing] = useState(focusOnMount);
  const [value, setValue] = useState(initialValue);
  const inputRef = useRef();
  const toggleEdit = () => {
    setEditing(!editing);
  };

  useEffect(() => {
    if (editing) {
      inputRef.current.focus();
    }
  }, [editing]);
  const save = e => {
    try {
      toggleEdit();
    } catch (errInfo) {
      console.log('Save failed:', errInfo);
    }
  };

  let childNode = value;
  if (editable) {
    childNode = editing ? (
      <div className="form-group"
      >
        <input ref={inputRef} onPressEnter={save} onBlur={save} value={value} onChange={(e) => setValue(e.target.value)} />
      </div>
    ) : (
        <button className="btn btn-default" style={{ paddingRight: 24 }} onClick={toggleEdit}>
          {value}
        </button>
      );
  }
  return <td {...restProps}>{childNode}</td>;
}

const domContainer = document.querySelector('#add-criterion-form');
ReactDOM.render(e(Form), domContainer);