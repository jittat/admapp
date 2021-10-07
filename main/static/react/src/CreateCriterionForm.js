'use strict';

const e = React.createElement
const { useState, useRef, useEffect } = React
let majors = JSON.parse(document.currentScript.getAttribute('data-majors'))
let dataRequired = JSON.parse(document.currentScript.getAttribute('data-required'))
let dataScoring = JSON.parse(document.currentScript.getAttribute('data-scoring'))
let dataSelectedMajors = JSON.parse(document.currentScript.getAttribute('data-selected-majors'))
let mode = document.currentScript.getAttribute('data-mode')
let _isCustomScoreCriteriaAllowed = document.currentScript.getAttribute('data-is_custom_score_criteria_allowed') === 'True'
const MODE = {
  CREATE: 'create',
  EDIT: 'edit'
}
const RELATION_MAX = "MAX"

const Form = () => {
  // console.log(dataRequired)
  // console.log(dataScoring)
  return (
    <div>
      <SelectMajors />
      {(!hideRequiredSection) && (
        <RequiredCriteria initialTopics={dataRequired || []} />
      )}
      <ScoringCriteria initialTopics={dataScoring || []} />
    </div>
  )
}
const SelectMajors = () => {
  const [selectedMajors, setSelectedMajors] = useState(dataSelectedMajors || [])
  const inputRef = useRef()
  const jRef = useRef()
  const choices = majors.map((m) => ({ label: m.title, value: m.id, raw: m }))
  // console.log(selectedMajors, dataSelectedMajors)
  // fix for jQuery
  jRef.current = { selectedMajors: selectedMajors }
  const toggleMajor = (major) => {
    const newSelectedMajors = jRef.current.selectedMajors.slice()
    const index = newSelectedMajors.findIndex((m) => m.id == major.id)
    if (index > -1) {
      newSelectedMajors.splice(index, 1)
    } else {
      newSelectedMajors.push(major)
    }
    setSelectedMajors(newSelectedMajors)
  }
  useEffect(() => {
    $(inputRef.current).autocomplete({
      source: choices,
      minLength: 0,
      select: (e, ui) => {
        toggleMajor(ui.item.raw);
        $(inputRef.current).blur()
        return false;
      },
    }).focus(function () {
      $(inputRef.current).autocomplete('search')
    })
  }, [])

  return (
    <div className="form-group">
      <label htmlFor="majors">เลือกสาขา</label>
      <input ref={inputRef} className="form-control d-inline-block mb-2" id="search-major" name="search" type="text" placeholder="ค้นหาชื่อสาขา" />
      {selectedMajors.length > 0 && <table className="table table-bordered">
        <thead>
          <tr>
            <th scope="col">สาขา</th>
            <th scope="col">จำนวนรับ (คน)</th>
            <th scope="col"></th>
          </tr>
        </thead>
        <tbody>
          {selectedMajors.map((major, idx) => {
            const label = major.title
            return (
              <tr key={`major-${major.id}`}>
                <td scope="row">{label}
                  <input value={major.id} type="hidden" name={`majors_${idx + 1}_id`} required />
                </td>
                <td><input type="number" className="form-control" name={`majors_${idx + 1}_slot`} defaultValue={major.slot} required /></td>
                <td><button htmltype="button" className="btn btn-secondary" onClick={() => toggleMajor(major)}>ลบ</button></td>
              </tr>
            )
          })}
        </tbody>
      </table>}
    </div>
  )
}
const RequiredCriteria = ({ initialTopics = [] }) => {
  const [topics, setTopics] = useState(initialTopics)
  const isCustomScoreCriteriaAllowed = _isCustomScoreCriteriaAllowed //from global variable
  const addNewTopic = (e) => {
    e.preventDefault()
    const newTopic = topics.slice()
    newTopic.push({ id: (() => Date.now())(), title: '', unit: '', children: [] })
    console.log(newTopic)
    setTopics(newTopic)
  }
  const updateTopic = (topicId, value) => {
    console.log(`Updating topic`, topicId, value)
    const newTopics = topics.slice()
    const index = newTopics.findIndex((t) => t.id === topicId)
    newTopics[index] = { ...newTopics[index], ...value }
    console.log('eiei', newTopics[index])
    setTopics(newTopics)
  }
  const removeTopic = (topic) => {
    const newTopics = topics.slice()
    const index = newTopics.findIndex((t) => t.id === topic.id)
    newTopics.splice(index, 1)
    setTopics(newTopics)
  }
  const setSecondaryTopics = (topicId, newSecondaryTopics) => {
    const newTopics = topics.slice()
    const index = newTopics.findIndex((t) => t.id === topicId)
    newTopics[index] = { ...newTopics[index], children: newSecondaryTopics }
    console.log('new topic', newTopics[index])
    setTopics(newTopics)
  }
  return (
    <div className="form-group" >
      <label htmlFor="majors">คุณสมบัติเฉพาะ</label>
      <small className="form-text text-muted">คุณสมบัติและคะแนนขั้นต่ำ เช่น ผลการเรียนเฉลี่ยสะสม ไม่น้อยกว่า 2.0</small>
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
            <PrimaryTopic
              key={topic.id}
              topic={topic}
              removeTopic={removeTopic}
              updateTopic={updateTopic}
              number={idx + 1}
              secondaryTopics={topic.children}
              setSecondaryTopics={(newSecondaryTopics) => setSecondaryTopics(topic.id, newSecondaryTopics)}
              isCustomScoreCriteriaAllowed={isCustomScoreCriteriaAllowed}
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

const ScoringCriteria = ({ initialTopics = [] }) => {
  const isCustomScoreCriteriaAllowed = _isCustomScoreCriteriaAllowed //from global variable

  const [topics, setTopics] = useState(initialTopics)

  const addNewTopic = (e) => {
    e.preventDefault()
    const newTopic = topics.slice()
    newTopic.push({ id: (() => Date.now())(), title: '', value: 1, children: [] })
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
      {(!useComponentWeightType) && (
        <small className="form-text text-muted">เกณฑ์สำหรับคำนวนคะแนน จัดลำดับ เช่น GAT 50%, PAT-1 50%  สำหรับรอบที่ 1 ถ้าไม่ต้องการระบุสัดส่วนให้ใส่ 0</small>
      )}
      {(useComponentWeightType) && (
        <small className="form-text text-muted">
          สำหรับเกณฑ์รอบ Admission 2 ให้เลือกแค่องค์ประกอบเดียว
          (ตอนนี้ในระบบอาจเลือกได้หลายเกณฑ์ แต่รบกวนเลือกแค่อันเดียวก่อน)
          ถ้ามีการรับหลายรูปแบบให้สร้างเงื่อนไขการรับเพิ่มเติม &nbsp;
          ถ้าต้องการแก้เกณฑ์ที่เลือกแล้วโดยการเลือกใหม่ ให้ลบข้อความทิ้งจะมีตัวเลือกขึ้นมาแสดงเหมือนเดิม
        </small>
      )}
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
              isCustomScoreCriteriaAllowed={isCustomScoreCriteriaAllowed}
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
const PrimaryTopic = ({ topic, removeTopic, number, updateTopic, secondaryTopics, setSecondaryTopics, isCustomScoreCriteriaAllowed }) => {
  const addNewTopic = (e) => {
    e.preventDefault()
    const newSecondaryTopics = secondaryTopics.slice()
    newSecondaryTopics.push({ id: (() => Date.now())(), title: '' })
    setSecondaryTopics(newSecondaryTopics)
  }
  const removeSecondaryTopic = (topic) => {
    const newSecondaryTopics = secondaryTopics.slice()
    const index = newSecondaryTopics.findIndex((t) => t.id === topic.id)
    newSecondaryTopics.splice(index, 1)
    setSecondaryTopics(newSecondaryTopics)
  }

  const updateSecondaryTopic = (topicId, value) => {
    const newSecondaryTopics = secondaryTopics.slice()
    const index = newSecondaryTopics.findIndex((t) => t.id === topicId)
    newSecondaryTopics[index] = { ...newSecondaryTopics[index], ...value }
    setSecondaryTopics(newSecondaryTopics)
  }

  const suffix = <div className="d-flex ml-2">
    {secondaryTopics.length > 0 && <SelectRelation name={`required_${number}_relation`} relations={relationRequired} className="ml-2" value={topic.relation} onChange={(event) => { event.target.value !== topic.relation && updateTopic(topic.id, { relation: event.target.value }) }} />}
    <button className="btn btn-primary btn-sm ml-2" onClick={addNewTopic}>+</button>
  </div>
  return (
    <React.Fragment>
      <tr>
        <td>
          {number}
        </td>
        {isCustomScoreCriteriaAllowed ? <EditableCell
          name={`required_${number}_title`}
          // editable={mode === MODE.CREATE}
          initialValue={topic.title}
          focusOnMount={true}
          suffix={suffix}
          inputProps={{ required: false }}
          tags={requiredTags}
          name={`required_${number}_title`}
          onSave={(v) => {
            const tag = requiredTags.find(o => o.description === v)
            updateTopic(topic.id, { score_type: tag ? tag.score_type : 'OTHER', unit: tag ? tag.unit : '' })
          }}
        /> :
          <td>
            <div className="d-flex align-items-baseline">
              <SelectMenu
                name={`required_${number}_title`}
                initialValue={topic.title}
                inputProps={{
                  required: false,
                }}
                choices={requiredTags.map(tag => ({
                  value: tag.description,
                  label: tag.description,
                  ...tag
                }))}

                onSave={(v) => {
                  const tag = requiredTags.find(o => o.description === v)
                  updateTopic(topic.id, { score_type: tag ? tag.score_type : 'OTHER', unit: tag ? tag.unit : '' })
                }}
              />
              {suffix}
            </div>
          </td>}
        <EditableCell
          name={`required_${number}_value`}
          // editable={mode === MODE.CREATE}
          initialValue={topic.value}
        />
        <EditableCell
          name={`required_${number}_unit`}
          editable={isCustomScoreCriteriaAllowed}
          initialValue={topic.unit || ''}
          tags={unitTags}
        />
        <input type="hidden" name={`required_${number}_type`} value={topic.score_type || "OTHER"} required />

        <td>
          <button className="btn btn-secondary btn-sm" onClick={() => removeTopic(topic)}>-</button>
        </td>
      </tr>
      {secondaryTopics.map((secondaryTopic, idx) => {
        const snumber = `${number}.${idx + 1}`
        const prefix = <span>{snumber}&nbsp;&nbsp;</span>
        return (
          <tr key={secondaryTopic.id}>
            <td></td>
            {isCustomScoreCriteriaAllowed ? <EditableCell
              name={`required_${snumber}_title`}
              // editable={mode === MODE.CREATE}
              initialValue={secondaryTopic.title}
              focusOnMount={true}
              prefix={prefix}
              inputProps={{ required: true }}
              tags={requiredTags}
              onSave={(v) => {
                const tag = requiredTags.find(o => o.description === v)
                updateSecondaryTopic(secondaryTopic.id, { ...secondaryTopic, score_type: tag ? tag.score_type : 'OTHER', unit: tag ? tag.unit : '' })
              }}
            /> :
              <td>
                <div className="d-flex align-items-baseline">
                  {prefix}
                  <SelectMenu
                    name={`required_${snumber}_title`}
                    initialValue={secondaryTopic.title}
                    inputProps={{ required: true }}
                    choices={requiredTags.map(tag => ({
                      value: tag.description,
                      label: tag.description,
                      ...tag
                    })
                    )
                    }

                    onSave={(v) => {
                      const tag = requiredTags.find(o => o.description === v)
                      updateSecondaryTopic(secondaryTopic.id, { ...secondaryTopic, score_type: tag ? tag.score_type : 'OTHER', unit: tag ? tag.unit : '' })
                    }}
                  />
                </div>
              </td>}
            <EditableCell
              name={`required_${snumber}_value`}
              // editable={mode === MODE.CREATE}
              initialValue={secondaryTopic.value}
            />
            <EditableCell
              name={`required_${snumber}_unit`}
              editable={isCustomScoreCriteriaAllowed}
              initialValue={secondaryTopic.unit}
              tags={unitTags}
            />
            <input type="hidden" name={`required_${snumber}_type`} value={secondaryTopic.score_type || "OTHER"} required />

            <td>
              <button className="btn btn-secondary btn-sm" onClick={() => removeSecondaryTopic(secondaryTopic)}>-</button>
            </td>
          </tr>
        )
      })}
    </React.Fragment>
  )
}
const PrimaryScoringTopic = ({ topic, removeTopic, number, updateTopic, maxScore, secondaryTopics, setSecondaryTopics, isCustomScoreCriteriaAllowed }) => {
  const addNewTopic = (e) => {
    e.preventDefault()
    const newSecondaryTopics = secondaryTopics.slice()
    newSecondaryTopics.push({ id: (() => (() => Date.now())())(), title: '', value: 1 })
    setSecondaryTopics(newSecondaryTopics)
  }
  const removeSecondaryTopic = (topic) => {
    const newSecondaryTopics = secondaryTopics.slice()
    const index = newSecondaryTopics.findIndex((t) => t.id === topic.id)
    newSecondaryTopics.splice(index, 1)
    setSecondaryTopics(newSecondaryTopics)
  }
  const updateSecondaryTopic = (topicId, value) => {
    const newSecondaryTopics = secondaryTopics.slice()
    const index = newSecondaryTopics.findIndex((t) => t.id === topicId)
    newSecondaryTopics[index] = { ...newSecondaryTopics[index], ...value }
    setSecondaryTopics(newSecondaryTopics)
  }
  const primaryMaxScore = secondaryTopics.reduce((a, b) => a + b.value, 0)
  const suffix = (
    <div className="d-flex">
      {secondaryTopics.length > 0 && <SelectRelation name={`scoring_${number}_relation`} relations={relationScoring} className="ml-2" value={topic.relation} onChange={(event) => { event.target.value !== topic.relation && updateTopic(topic.id, { relation: event.target.value }) }} />}
      <button className="btn btn-primary btn-sm ml-2" onClick={addNewTopic}>+</button>
    </div>)
  return (
    <React.Fragment>
      <tr>
        <td>
          {number}
        </td>
        {isCustomScoreCriteriaAllowed ? <EditableCell
          name={`scoring_${number}_title`}
          // editable={mode === MODE.CREATE}
          initialValue={topic.title}
          focusOnMount={true}
          suffix={suffix}
          inputProps={{ required: false }}
          tags={scoringTags}
          onSave={(v) => {
            const tag = scoringTags.find(o => o.description === v)
            updateTopic(topic.id, { score_type: tag ? tag.score_type : 'OTHER' })
          }}
        /> :
          <td>
            <div className="d-flex align-items-baseline">
              <SelectMenu
                name={`scoring_${number}_title`}
                initialValue={topic.title}
                inputProps={{
                  required: false,
                }}
                choices={scoringTags.map(tag => ({
                  value: tag.description,
                  label: tag.description,
                  ...tag
                }))}

                onSave={(v) => {
                  const tag = scoringTags.find(o => o.description === v)
                  updateTopic(topic.id, { score_type: tag ? tag.score_type : 'OTHER' })
                }}
              />
              {suffix}
            </div>
          </td>
        }
        <EditableCell
          name={`scoring_${number}_value`}
          // editable={mode === MODE.CREATE}
          initialValue={topic.value}
          onSave={(v) => { updateTopic(topic.id, { value: parseInt(v) }) }}
          inputType="number"
          inputProps={{ required: true }}
        />
        <input type="hidden" name={`scoring_${number}_type`} value={topic.score_type || "OTHER"} required />

        <td><strong>{(topic.value / maxScore * 100).toLocaleString()}%</strong></td>
        <td>
          <button className="btn btn-secondary btn-sm" onClick={() => removeTopic(topic)}>-</button>
        </td>
      </tr>
      {secondaryTopics.map((secondaryTopic, idx) => {
        const snumber = `${number}.${idx + 1}`
        const prefix = <span>{number}.{idx + 1}&nbsp;&nbsp;</span>
        return (
          <tr key={secondaryTopic.id}>
            <td></td>
            {isCustomScoreCriteriaAllowed ? <EditableCell
              name={`scoring_${snumber}_title`}
              // editable={mode === MODE.CREATE}
              initialValue={secondaryTopic.title}
              focusOnMount={true}
              prefix={prefix}
              inputProps={{ required: true }}
              tags={scoringTags}

              onSave={(v) => {
                const tag = scoringTags.find(o => o.description === v)
                updateSecondaryTopic(secondaryTopic.id, { ...secondaryTopic, score_type: tag ? tag.score_type : 'OTHER' })
              }}
            /> :

              <td>
                <div className="d-flex align-items-baseline">
                  {prefix}
                  <SelectMenu
                    name={`scoring_${snumber}_title`}
                    initialValue={secondaryTopic.title}
                    inputProps={{
                      required: true,
                    }}
                    choices={scoringTags.map(tag => ({
                      value: tag.description,
                      label: tag.description,
                      ...tag
                    }))}

                    onSave={(v) => {
                      const tag = scoringTags.find(o => o.description === v)
                      updateSecondaryTopic(secondaryTopic.id, { ...secondaryTopic, score_type: tag ? tag.score_type : 'OTHER' })
                    }}
                  />
                </div>
              </td>}
            {topic.relation === RELATION_MAX ? <td></td> : <EditableCell
              name={`scoring_${snumber}_value`}
              // editable={mode === MODE.CREATE}
              initialValue={secondaryTopic.value}
              onSave={(v) => { updateSecondaryTopic(secondaryTopic.id, { value: parseInt(v) }) }}
              inputType="number"
              inputProps={{ required: true }}
            />}
            <input type="hidden" name={`scoring_${snumber}_type`} value={secondaryTopic.score_type || "OTHER"} required />

            <td>{topic.relation !== RELATION_MAX && `${(secondaryTopic.value / primaryMaxScore * 100).toLocaleString()}%`}</td>
            <td>
              <button className="btn btn-secondary btn-sm" onClick={() => removeSecondaryTopic(secondaryTopic)}>-</button>
            </td>
          </tr>
        )
      })}
    </React.Fragment>
  )
}
const EditableCell = ({
  value,
  initialValue,
  editable = true,
  focusOnMount = false,
  children,
  onSave,
  prefix,
  suffix,
  inputType,
  name,
  inputProps,
  tags = [],
  ...restProps }) => {
  const inputRef = useRef();
  useEffect(() => {
    if (editable) {
      $(inputRef.current).autocomplete({
        source: typeof (tags[0]) === 'string' ? tags :
          // for required and scoring tags
          // TODO: refactor this
          tags.map(o => ({
            label: o.description,
            value: o.description,
            onSelect: () => {

              let temp = name.split('_')
              temp[temp.length - 1] = 'unit'
              const unitName = temp.join('_')
              const unitEl = $(`[name="${unitName}"]`)[0]

              if (unitEl) {
                unitEl.value = o.unit
              }
            }
          })),
        minLength: 0,
        select: ((event, ui) => {
          ui.item.onSelect && ui.item.onSelect()
        })
      }).focus(function () {
        if (inputRef.current.value == "") {
          $(inputRef.current).autocomplete("search");
        }
      })
    } else {

    }
  }, [editable])

  useEffect(() => {
    if (focusOnMount && !initialValue) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [focusOnMount]);
  const save = e => {
    try {
      onSave && onSave(inputRef.current.value)
    } catch (errInfo) {
      console.log('Save failed:', errInfo);
    }
  };

  const calHeight = () => {
    inputRef.current.style.height = ""
    inputRef.current.style.height = inputRef.current.scrollHeight + 'px'
  }
  useEffect(() => { if (editable) { calHeight() } }, [])
  let childNode = (
    <input type={inputType} name={name} className="form-control d-inline-block" defaultValue={initialValue} tabIndex={-1} style={{ pointerEvents: 'none' }} {...inputProps} />
  )
  if (editable) {
    childNode =
      (
        <div className="d-flex align-items-baseline">
          {prefix}
          {inputType === 'number' ? (
            <input type="number" name={name} className="form-control d-inline-block" ref={inputRef} onChange={save} onBlur={save} defaultValue={initialValue} {...inputProps} />
          ) :
            (
              <textarea className="form-control d-inline-block" rows={1} name={name} ref={inputRef} onChange={calHeight} onBlur={save} defaultValue={initialValue} {...inputProps} />
            )
          }
          {suffix}
        </div>
      )
  }
  return <td style={editable ? { cursor: 'pointer' } : {}} {...restProps}> {childNode}</td >;
}
const SelectRelation = ({ name, relations, className, value, onChange }) => {
  return (<select name={name} id={name} className={className} value={value} onChange={onChange}>
    <option disabled selected value="">เลือกความสัมพันธ์</option>
    {relations.map(r => (<option value={r.value} key={r.value}>{r.label}</option>))}
  </select>)
}

const SelectMenu = ({ name, choices, className, initialValue, inputProps, onSave }) => {
  const inputRef = useRef();
  useEffect(() => {
    $(inputRef.current).selectmenu({
      classes: { 'ui-selectmenu-button': 'flex-1' },
      select: ((event, ui) => {
        onSave && onSave(inputRef.current.value)

        const name = event.target.name
        const o = choices.find(choice => choice.value === ui.item.value)
        // console.log('name: ', name)
        // console.log('o: ', o)
        if (!o) return

        let temp = name.split('_')
        temp[temp.length - 1] = 'unit'
        const unitName = temp.join('_')
        const unitEl = $(`[name="${unitName}"]`)[0]
        if (unitEl) {
          unitEl.value = o.unit
        }
      }
      )
    }).selectmenu("menuWidget").addClass("overflow");
  }, [])
  return (
    <select name={name} id={name} defaultValue={initialValue || null} ref={inputRef} rows={1} {...inputProps}>
      <option disabled={inputProps.required} selected value="" key="">{inputProps.required ? 'กรุณาเลือก' : ''}</option>
      {choices.map(r => (<option value={r.value} key={r.value}>{r.label}</option>
      ))}
    </select>)
}

const domContainer = document.querySelector('#add-criterion-form');
ReactDOM.render(e(Form), domContainer);
