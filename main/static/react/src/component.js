'use strict';

const e = React.createElement
const { useState, useRef, useEffect } = React
let majors = JSON.parse(document.currentScript.getAttribute('data-majors'))
const Form = () => {
  const [search, setSearch] = useState('')
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
        <RequiredCriteria />
        <ScoringCriteria />
      </form>
    </div>
  )
}
const RequiredCriteria = () => {
  const [topics, setTopics] = useState([
    { id: 1, title: 'PAT 1', value: 22, unit: 'หน่วยกิต' },
    { id: 2, title: 'PAT 2', value: 22, unit: 'หน่วยกิต', children: [{ id: 2.1, title: 'PAT 2.2', value: 22, unit: 'หน่วยกิต' }] }])

  const addNewTopic = (topic) => {
    const newTopic = topics.slice()
    newTopic.push({ id: Date.now(), title: '', value: '', unit: '' })
    setTopics(newTopic)
  }
  const removeTopic = (topic) => {
    const newTopics = topics.slice()
    const index = newTopics.findIndex((t) => t.id === topic.id)
    newTopics.splice(index, 1)
    setTopics(newTopics)
  }
  return (
    <div className="form-group" >
      <label htmlFor="majors">คุณสมบัติเฉพาะ</label>
      <small className="form-text text-muted">คุณสมบัติและคะแนนขั้นต่ำ เช่น O-NET ภาษาอังกฤษ มากกว่า 16 คะแนน</small>
      {/* TODO: add known criteria */}
      <table className="table table-bordered" style={{ tableLayout: 'fixed' }}>
        <thead>
          <tr>
            <th style={{ width: '5%' }}></th>
            <th></th>
            <th style={{ width: '15%' }}>ขั้นต่ำ (≥)</th>
            <th style={{ width: '15%' }}>หน่วย</th>
            <th style={{ width: '5%' }}></th>
          </tr>
        </thead>
        <tbody>
          {topics.map((topic, idx) =>
            <PrimaryTopic key={topic.id} topic={topic} removeTopic={removeTopic} number={idx + 1} />
          )}
          <tr>
            <td>
              <div className="btn btn-primary" onClick={addNewTopic}>+</div>
            </td>
            <td></td>
            <td></td>
            <td></td>
            <td></td>
          </tr>
        </tbody>
      </table>
    </div>)
}

const ScoringCriteria = () => {
  const [topics, setTopics] = useState([
    { id: 1, title: 'ผลการเรียนเฉลี่ยสะสม (GPAX)', value: 1, children: [{ id: 1.1, title: 'ผลการเรียนเฉลี่ยสะสม (GPAX)', value: 1 }] },
    { id: 2, title: 'การสอบปฏิบัติเครื่องดนตรีตะวันตก', value: 1, children: [{ id: 2.1, title: 'ความรู้พื้นฐานทางทฤษฎีและประวัติศาสตร์ดนตรีตะวันตก', value: 1 }] }])

  const addNewTopic = () => {
    const newTopic = topics.slice()
    newTopic.push({ id: Date.now(), title: '', value: 1, children: [] })
    console.log(newTopic)
    setTopics(newTopic)
  }
  const removeTopic = (topic) => {
    const newTopics = topics.slice()
    const index = newTopics.findIndex((t) => t.id === topic.id)
    newTopics.splice(index, 1)
    setTopics(newTopics)
  }
  const updateTopic = (topicId, value) => {
    console.log(`Updating topic`, topicId, value)
    const newTopics = topics.slice()
    const index = newTopics.findIndex((t) => t.id === topicId)
    newTopics[index] = { ...newTopics[index], ...value }
    setTopics(newTopics)
  }
  const setSecondaryTopics = (topicId, newSecondaryTopics) => {
    const newTopics = topics.slice()
    const index = newTopics.findIndex((t) => t.id === topicId)
    newTopics[index] = { ...newTopics[index], children: newSecondaryTopics }
    setTopics(newTopics)
  }
  const maxScore = topics.reduce((a, b) => a + b.value, 0)
  return (
    <div className="form-group" >
      <label htmlFor="majors">เกณฑ์การคัดเลือก</label>
      <small className="form-text text-muted">เกณฑ์สำหรับคำนวนคะแนน จัดลำดับ เช่น GAT 50%, PAT-1 50%</small>
      {/* TODO: add known criteria */}
      <table className="table table-bordered" style={{ tableLayout: 'fixed' }}>
        <thead>
          <tr>
            <th style={{ width: '5%' }}></th>
            <th></th>
            <th style={{ width: '15%' }}>สัดส่วนคะแนน</th>
            <th style={{ width: '15%' }}>ร้อยละ</th>
            <th style={{ width: '5%' }}></th>
          </tr>
        </thead>
        <tbody>
          {topics.map((topic, idx) =>
            <PrimaryScoringTopic
              topic={topic}
              updateTopic={updateTopic}
              removeTopic={removeTopic}
              number={idx + 1}
              maxScore={maxScore}
              secondaryTopics={topic.children}
              setSecondaryTopics={(newSecondaryTopics) => setSecondaryTopics(topic.id, newSecondaryTopics)}
              key={topic.id}
            />
          )}
          <tr>
            <td>
              <div className="btn btn-primary" onClick={addNewTopic}>+</div>
            </td>
            <td></td>
            <td></td>
            <td></td>
            <td></td>
          </tr>
        </tbody>
      </table>
    </div>)
}
const PrimaryTopic = ({ topic, removeTopic, number }) => {
  const [secondaryTopics, setSecondaryTopics] = useState([])
  const addNewTopic = () => {
    const newSecondaryTopics = secondaryTopics.slice()
    newSecondaryTopics.push({ id: Date.now(), title: '', value: '', unit: '' })
    setSecondaryTopics(newSecondaryTopics)
  }

  const removeSecondaryTopic = (topic) => {
    const newSecondaryTopics = secondaryTopics.slice()
    const index = newSecondaryTopics.findIndex((t) => t.id === topic.id)
    newSecondaryTopics.splice(index, 1)
    setSecondaryTopics(newSecondaryTopics)
  }
  return (
    <React.Fragment>
      <tr>
        <td>
          {number}
        </td>
        <EditableCell initialValue={topic.title} focusOnMount={true} suffix={
          <div>
            <button className="btn btn-primary btn-sm" onClick={addNewTopic}>+</button>
          </div>
        } />
        <EditableCell initialValue={topic.value} />
        <EditableCell initialValue={topic.unit} />
        <td>
          <button className="btn btn-secondary btn-sm" onClick={() => removeTopic(topic)}>-</button>
        </td>
      </tr>
      {secondaryTopics.map((topic, idx) => (
        <tr key={topic.id}>
          <td></td>
          <EditableCell initialValue={topic.title} focusOnMount={true} prefix={<span>&nbsp;	&nbsp;	&nbsp;	&nbsp;{number}.{idx + 1}&nbsp;&nbsp;</span>} />
          <EditableCell initialValue={topic.value} />
          <EditableCell initialValue={topic.unit} />
          <td>
            <button className="btn btn-secondary btn-sm" onClick={() => removeSecondaryTopic(topic)}>-</button>
          </td>
        </tr>
      ))}
    </React.Fragment>
  )
}
const PrimaryScoringTopic = ({ topic, removeTopic, number, updateTopic, maxScore, secondaryTopics, setSecondaryTopics }) => {
  const addNewTopic = (e) => {
    console.log('eiei')
    // e.stopPropagation()
    const newSecondaryTopics = secondaryTopics.slice()
    newSecondaryTopics.push({ id: Date.now(), title: '', value: 1 })
    console.log('addNewTopic', newSecondaryTopics)
    setSecondaryTopics(newSecondaryTopics)
  }
  const removeSecondaryTopic = (topic) => {
    const newSecondaryTopics = secondaryTopics.slice()
    const index = newSecondaryTopics.findIndex((t) => t.id === topic.id)
    newSecondaryTopics.splice(index, 1)
    setSecondaryTopics(newSecondaryTopics)
  }
  return (
    <React.Fragment>
      <tr>
        <td>
          {number}
        </td>
        <EditableCell initialValue={topic.title} focusOnMount={true} suffix={
          <div>
            <button className="btn btn-primary btn-sm" onClick={addNewTopic}>+</button>
          </div>
        } />
        <EditableCell initialValue={topic.value} onSave={(v) => { updateTopic(topic.id, { value: v }) }} inputType="number" />
        <td>{(topic.value / maxScore * 100).toPrecision(2)}%</td>
        <td>
          <button className="btn btn-secondary btn-sm" onClick={() => removeTopic(topic)}>-</button>
        </td>
      </tr>
      {secondaryTopics.map((topic, idx) => (
        <tr key={topic.id}>
          <td></td>
          <EditableCell initialValue={topic.title} focusOnMount={true} prefix={<span>&nbsp;	&nbsp;	&nbsp;	&nbsp;{number}.{idx + 1}&nbsp;&nbsp;</span>} />
          <EditableCell initialValue={topic.value} />
          <td>3%</td>
          <td>
            <button className="btn btn-secondary btn-sm" onClick={() => removeSecondaryTopic(topic)}>-</button>
          </td>
        </tr>
      ))}
    </React.Fragment>
  )
}
const EditableCell = ({
  initialValue,
  editable = true,
  focusOnMount = false,
  children,
  onSave,
  prefix,
  suffix,
  inputType,
  ...restProps }) => {
  const [editing, setEditing] = useState(focusOnMount);
  const [value, setValue] = useState(initialValue);
  const inputRef = useRef();
  const toggleEdit = () => {
    setEditing(!editing);
  };
  useEffect(() => {
    var availableTags = [
      "ActionScript",
      "AppleScript",
      "Asp",
      "BASIC",
      "C",
      "C++",
      "Clojure",
      "COBOL",
      "ColdFusion",
      "Erlang",
      "Fortran",
      "Groovy",
      "Haskell",
      "Java",
      "JavaScript",
      "Lisp",
      "Perl",
      "PHP",
      "Python",
      "Ruby",
      "Scala",
      "Scheme"
    ];
    if (editing) {
      $(inputRef.current).autocomplete({
        source: availableTags
      });
    }
  }, [editing])

  useEffect(() => {
    if (editing) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [editing]);
  const save = e => {
    try {
      toggleEdit();
      setValue(inputRef.current.value)
      onSave && onSave(inputRef.current.value)
    } catch (errInfo) {
      console.log('Save failed:', errInfo);
    }
  };

  let childNode = value
  if (editable) {
    childNode = editing ? (
      <div className="form-group d-flex"
      >
        {prefix}
        {inputType === 'number' ? (
          <input type="text" className="form-control d-inline-block" ref={inputRef} onPressEnter={save} onBlur={save} defaultValue={value} />
        ) :
          (
            <textarea className="form-control  d-inline-block" ref={inputRef} onPressEnter={save} onBlur={save} defaultValue={value} />
          )
        }
      </div>
    ) : (
        <div className="form-group d-flex">
          <button className="btn" style={{ textAlign: 'left', width: '100%', whiteSpace: 'pre-wrap' }} onClick={toggleEdit}>
            {prefix}{value}
          </button>
          {suffix}
        </div>
      );
  }
  return <td onClick={toggleEdit} style={{ cursor: 'pointer' }} {...restProps}> {childNode}</td >;
}

const domContainer = document.querySelector('#add-criterion-form');
ReactDOM.render(e(Form), domContainer);