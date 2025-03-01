# CanadaSolarConnect
This project is a system that accesses the API server operating on CanadianSolar power units to retrieve power information. Verified power detection unit: CSPDUE

## Item Description

| No | Item Name  | Description                                                           |
|----|------------|-----------------------------------------------------------------------|
| 1  | ipaddress  | Address of the power detection unit (CSPDUE)                          |
| 2  | 24080038   | Serial number??                                                       |
| 3  | PC1f7eed87-b | Session ID?                                                          |
| 4  | 20250206&20250206 | Start date and time to end date and time?                      |
| 5  | Z02        | Request/response identifier? Sequence number                          |
| 6  | V2HST      |                                                                       |
| 7  | DST        |                                                                       |
| 8  | IEVD       | Inverter related? Voltage                                             |
| 9  | IEVC       | Inverter related? Current                                             |
| 10 | IEVR       | Inverter related? Power                                               |
| 11 | IG0        | Generated power [kW]                                                  |
| 12 | IBE        | Purchased power [kW]                                                  |
| 13 | ISE        | Sold power [kW]?                                                      |
| 14 | ICE        | Consumed power [kW]                                                   |
| 15 | TG0        | Total generated power [kWh]?                                          |
| 16 | IDD        |                                                                       |
| 17 | IDC        |                                                                       |
| 18 | IDR        |                                                                       |
| 19 | IGE        |                                                                       |

## API Endpoints

### GET /getinfo

Retrieve power information from the CanadianSolar power unit.

#### Query Parameters

| Parameter       | Type   | Description                                                                 |
|-----------------|--------|-----------------------------------------------------------------------------|
| `startDate`     | string | (Optional) Start date in `YYYYMMDD` format. Defaults to current date.       |
| `endDate`       | string | (Optional) End date in `YYYYMMDD` format. Defaults to current date.         |
| `sequenceCounter` | int  | (Optional) Sequence counter. If not provided, an internal counter is used.  |
| `getParams`     | string | (Optional) Parameters to retrieve. Defaults to `V2HST&DST&IEVD&IEVC&IEVR&IG0&IBE&ISE&ICE&TG0&IDD&IDC&IDR&IGE`. |

#### Response

- `200 OK`: Returns the power information in JSON format.
- `4xx/5xx`: Returns an error message with the status code.

#### Example Request

```
GET /getinfo?startDate=20250301&endDate=20250301&sequenceCounter=1&getParams=V2HST&DST&IEVD&IEVC&IEVR&IG0&IBE&ISE&ICE&TG0&IDD&IDC&IDR&IGE
```

#### Example Response

```json
{
  "00000000000000": null,
  "16640": null,
  "20250301": null,
  "24080038": null,
  "DST": "-2",
  "IBE": "0.0",
  "ICE": "2.0",
  "IDC": "0.0",
  "IDD": "0.0",
  "IDR": "0",
  "IEVC": "-1",
  "IEVD": "-1",
  "IEVR": "0",
  "IG0": "3.4",
  "IGE": "3380",
  "ISE": "1.4",
  "TG0": "6.0",
  "V2HST": "-2",
  "Z1": null
}
