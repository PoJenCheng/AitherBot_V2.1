// 軸物件的設置 vtkOrientationMarkerWidget、vtkAnnotatedCubeActor、vtkAxesActor

// 使用範例1  出處：https://smili-project.sourceforge.io/api/milx_qt_render_window_8cpp_source.html

void milxQtRenderWindow::setupHumanGlyph(vtkSmartPointer<vtkMatrix4x4> mat)
 {
     vtkSmartPointer<vtkPolyData> human;
     openModelUsingQt(":/resources/human.obj", human); //needs to be done usingQt method to access model as a resource
 
     vtkSmartPointer<vtkPolyData> humanTransformed;
     if(mat)
     {
         vtkSmartPointer<vtkTransform> transf = vtkSmartPointer<vtkTransform>::New();
             transf->SetMatrix(mat);
 
         vtkSmartPointer<vtkTransformPolyDataFilter> transformer = vtkSmartPointer<vtkTransformPolyDataFilter>::New();
         #if VTK_MAJOR_VERSION <= 5
             transformer->SetInput(human);
         #else
             transformer->SetInputData(human);
         #endif
             transformer->SetTransform(transf);
             transformer->Update();
 
         vtkSmartPointer<vtkPolyDataNormals> normalsHuman = vtkSmartPointer<vtkPolyDataNormals>::New();
             #if VTK_MAJOR_VERSION <= 5
             normalsHuman->SetInput(transformer->GetOutput());
         #else
             normalsHuman->SetInputData(transformer->GetOutput());
         #endif
             normalsHuman->Update();
 
         humanTransformed = normalsHuman->GetOutput();
     }
     else
         humanTransformed = human;
 
     vtkSmartPointer<vtkPropAssembly> propAssembly = vtkSmartPointer<vtkPropAssembly>::New();
     orientAxes = vtkSmartPointer<vtkAxesActor>::New();
 
     if(orientationAxes)
     {
         orientAxes->GetXAxisCaptionActor2D()->GetCaptionTextProperty()->ShadowOff();
         orientAxes->GetXAxisCaptionActor2D()->GetCaptionTextProperty()->SetFontSize(14);
         orientAxes->GetXAxisCaptionActor2D()->GetTextActor()->SetTextScaleModeToNone();
         orientAxes->GetYAxisCaptionActor2D()->GetCaptionTextProperty()->ShadowOff();
         orientAxes->GetYAxisCaptionActor2D()->GetCaptionTextProperty()->SetFontSize(14);
         orientAxes->GetYAxisCaptionActor2D()->GetTextActor()->SetTextScaleModeToNone();
         orientAxes->GetZAxisCaptionActor2D()->GetCaptionTextProperty()->ShadowOff();
         orientAxes->GetZAxisCaptionActor2D()->GetCaptionTextProperty()->SetFontSize(14);
         orientAxes->GetZAxisCaptionActor2D()->GetTextActor()->SetTextScaleModeToNone();
         orientAxes->SetXAxisLabelText("Left");
         orientAxes->SetYAxisLabelText("P");
         orientAxes->SetZAxisLabelText("S");
 
         if(mat)
             orientAxes->SetUserMatrix(mat);
 
         propAssembly->AddPart(orientAxes);
     }
 
     vtkSmartPointer<vtkPolyDataMapper> humanMapper = vtkSmartPointer<vtkPolyDataMapper>::New();
     #if VTK_MAJOR_VERSION <= 5
         humanMapper->SetInput(humanTransformed);
     #else
         humanMapper->SetInputData(humanTransformed);
     #endif
     vtkSmartPointer<vtkActor> humanActor = vtkSmartPointer<vtkActor>::New();
         humanActor->SetMapper(humanMapper);
         humanActor->GetProperty()->SetInterpolationToPhong();
 //        humanActor->GetProperty()->SetColor(235/255.0, 180/255.0, 173/255.0); //skin
         humanActor->GetProperty()->SetColor(60/255.0, 232/255.0, 30/255.0); //Varian Eclipse green
     propAssembly->AddPart(humanActor);
     humanGlyph = vtkSmartPointer<vtkOrientationMarkerWidget>::New();
         humanGlyph->SetOutlineColor(0.0, 0, 0.0);
         humanGlyph->SetOrientationMarker(propAssembly);
         humanGlyph->SetInteractor(QVTKWidget::GetInteractor());
         humanGlyph->SetViewport(0.0, 0.0, 0.3, 0.3);
         humanGlyph->SetDefaultRenderer(renderer);
 }

 // 使用範例 2
 https://blog.csdn.net/liushao1031177/article/details/118275745