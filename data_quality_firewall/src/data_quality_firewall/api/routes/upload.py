from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
import uuid
import csv
from io import StringIO
from data_quality_firewall.db.session import get_db
from data_quality_firewall.models.run import FileRun

router = APIRouter(prefix="/files", tags=["files"])




@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files allowed")

    # Create initial run
    new_run = FileRun(
        id=uuid.uuid4(),
        filename=file.filename,
        status="PROCESSING"
    )

    db.add(new_run)
    db.commit()
    db.refresh(new_run)

    # Read file contents
    contents = await file.read()
    decoded = contents.decode("utf-8")
    csv_reader = csv.reader(StringIO(decoded))

    total_rows = 0
    valid_rows = 0
    invalid_rows = 0

    header = next(csv_reader, None)

    for row in csv_reader:
        total_rows += 1

        # Simple validation rule:
        # Row is valid if no empty values
        if all(cell.strip() != "" for cell in row):
            valid_rows += 1
        else:
            invalid_rows += 1

    # Update run with results
    new_run.total_rows = total_rows
    new_run.valid_rows = valid_rows
    new_run.invalid_rows = invalid_rows
    new_run.status = "COMPLETED"

    db.commit()
    db.refresh(new_run)

    return {
        "run_id": str(new_run.id),
        "filename": new_run.filename,
        "status": new_run.status,
        "total_rows": new_run.total_rows,
        "valid_rows": new_run.valid_rows,
        "invalid_rows": new_run.invalid_rows,
    }
