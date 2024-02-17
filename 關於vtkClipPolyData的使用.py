# 關於vtkClipPolyData的使用
# 重點：vtkPlanes *frustum = static_cast<vtkAreaPicker*>(this->GetInteractor()->GetPicker())->GetFrustum(); // 獲得框選矩形
# vtkClipPolyData *clipper = vtkClipPolyData::New();
# clipper->SetInputData(this->Data);
# clipper->SetClipFunction(frustum); //重要！自定隱函數
# clipper->GenerateClipScalarsOn();
# clipper->GenerateClippedOutputOn();
# clipper->SetValue(0.5)
# this->selectedMapper->SetInputConnection(clipper->GetOutputPort());
# this->selectedMapper->ScalarVisibilityOff();
# this->selectedActor->SetMapper(selectedMapper);
# this->selectedActor->GetProperty()->SetColor(1.0, 0.0, 0.0);
# this->selectedActor->GetProperty()->SetRepresentationToWireframe();

https://blog.csdn.net/q610098308/article/details/107971701